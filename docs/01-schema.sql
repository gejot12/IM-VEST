-- IM-VEST Intelligence — schema v1 (PostgreSQL 16 + PostGIS)
-- Konvensi: id bigint identity, waktu timestamptz, enum = text + CHECK (mudah diubah tanpa migrasi tipe).
CREATE EXTENSION IF NOT EXISTS postgis;

-- ───────── Auth ─────────
CREATE TABLE users (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email text UNIQUE NOT NULL,
  password_hash text NOT NULL,
  role text NOT NULL CHECK (role IN ('ADMIN','ANALYST','RM','INVESTOR')),
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ───────── Provenance (wajib: setiap fakta punya sumber) ─────────
CREATE TABLE data_sources (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name text NOT NULL,
  provider text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN ('OFFICIAL','PUBLIC','THIRD_PARTY','SEED','MANUAL')),
  api_url text,
  license text,
  refresh_frequency text,
  reliability_score numeric(3,2) CHECK (reliability_score BETWEEN 0 AND 1)
);
CREATE TABLE data_ingestion_logs (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_id bigint NOT NULL REFERENCES data_sources,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  status text NOT NULL CHECK (status IN ('RUNNING','OK','FAILED')),
  rows_written int DEFAULT 0,
  error text
);

-- ───────── Market master ─────────
CREATE TABLE sectors (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  code text UNIQUE NOT NULL,
  name text NOT NULL
);
CREATE TABLE industries (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sector_id bigint NOT NULL REFERENCES sectors,
  name text NOT NULL
);
CREATE TABLE commodities (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  code text UNIQUE NOT NULL,   -- NICKEL, COAL, CPO, GOLD, OIL, COPPER
  name text NOT NULL,
  unit text
);
CREATE TABLE companies (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ticker text UNIQUE,                       -- NULL jika tidak listed
  name text NOT NULL,
  short_name text,
  sector_id bigint REFERENCES sectors,
  industry_id bigint REFERENCES industries,
  description text,
  website text,
  is_listed boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
-- Market cap SENGAJA tidak di companies: itu data berwaktu, hitung dari prices + shares.
CREATE TABLE securities (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  company_id bigint NOT NULL REFERENCES companies,
  ticker text NOT NULL,
  security_type text NOT NULL CHECK (security_type IN ('EQUITY','BOND','FUND','INDEX','FX','COMMODITY')),
  exchange text NOT NULL DEFAULT 'IDX',
  currency text NOT NULL DEFAULT 'IDR',
  isin text,
  status text NOT NULL DEFAULT 'ACTIVE',
  UNIQUE (exchange, ticker)
);
CREATE TABLE prices (
  security_id bigint NOT NULL REFERENCES securities,
  ts timestamptz NOT NULL,
  open numeric, high numeric, low numeric, close numeric NOT NULL,
  volume bigint, value numeric,
  source_id bigint NOT NULL REFERENCES data_sources,
  PRIMARY KEY (security_id, ts)
);
CREATE TABLE fundamentals (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  company_id bigint NOT NULL REFERENCES companies,
  period text NOT NULL,                     -- '2025-Q4', '2025-FY'
  revenue numeric, ebitda numeric, net_income numeric,
  assets numeric, liabilities numeric, equity numeric,
  cash numeric, debt numeric, eps numeric, book_value numeric,
  roe numeric, roa numeric,
  source_id bigint NOT NULL REFERENCES data_sources,
  UNIQUE (company_id, period)
);
CREATE TABLE corporate_actions (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  company_id bigint NOT NULL REFERENCES companies,
  action_type text NOT NULL,                -- DIVIDEND, SPLIT, RIGHTS, BUYBACK
  announced_at date, effective_at date,
  detail jsonb,
  source_id bigint REFERENCES data_sources
);

-- ───────── Geo ─────────
CREATE TABLE locations (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name text NOT NULL,
  location_type text NOT NULL,
  geom geography(Point,4326) NOT NULL,
  country text DEFAULT 'ID', province text, city text, address text,
  source_id bigint NOT NULL REFERENCES data_sources,
  verified_at timestamptz                   -- NULL = belum diverifikasi, UI wajib menandai
);
CREATE INDEX locations_geom_idx ON locations USING gist (geom);
CREATE TABLE company_locations (
  company_id bigint NOT NULL REFERENCES companies,
  location_id bigint NOT NULL REFERENCES locations,
  relationship_type text NOT NULL,          -- HQ, OPERATES, OWNS
  ownership_pct numeric(5,2),
  status text, start_date date, end_date date,
  PRIMARY KEY (company_id, location_id, relationship_type)
);
CREATE TABLE assets (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  company_id bigint NOT NULL REFERENCES companies,
  asset_type text NOT NULL CHECK (asset_type IN
    ('MINE','SMELTER','FACTORY','WAREHOUSE','PORT','POWER_PLANT','OFFICE','PROJECT')),
  name text NOT NULL,
  location_id bigint REFERENCES locations,
  commodity_id bigint REFERENCES commodities,
  capacity text,
  status text,
  source_id bigint NOT NULL REFERENCES data_sources,
  verified_at timestamptz
);
-- Fase 2, tabel disiapkan agar tidak migrasi besar nanti.
CREATE TABLE supply_chain_nodes (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  commodity_id bigint REFERENCES commodities,
  stage text NOT NULL,                      -- MINING, PROCESSING, SMELTER, MATERIAL, PRODUCT
  asset_id bigint REFERENCES assets
);
CREATE TABLE supply_chain_edges (
  from_node bigint NOT NULL REFERENCES supply_chain_nodes,
  to_node bigint NOT NULL REFERENCES supply_chain_nodes,
  PRIMARY KEY (from_node, to_node)
);

-- ───────── News, events, impact ─────────
CREATE TABLE news (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title text NOT NULL, summary text, url text UNIQUE NOT NULL,
  publisher text, published_at timestamptz NOT NULL, language text,
  sentiment text CHECK (sentiment IN ('POSITIVE','NEUTRAL','NEGATIVE')),
  impact_score numeric(4,3),
  source_id bigint REFERENCES data_sources,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE news_entities (
  news_id bigint NOT NULL REFERENCES news,
  entity_type text NOT NULL CHECK (entity_type IN ('COMPANY','SECTOR','COMMODITY','COUNTRY')),
  entity_id bigint NOT NULL,
  relevance_score numeric(4,3),
  impact text CHECK (impact IN ('POSITIVE','NEUTRAL','NEGATIVE')),
  PRIMARY KEY (news_id, entity_type, entity_id)
);
CREATE TABLE events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_type text NOT NULL CHECK (event_type IN
    ('POLICY','COMMODITY','WEATHER','DISASTER','CORPORATE','MACRO','GEOPOLITICAL')),
  title text NOT NULL, description text,
  ts timestamptz NOT NULL,
  impact_score numeric(4,3), confidence text CHECK (confidence IN ('HIGH','MEDIUM','LOW')),
  source_id bigint REFERENCES data_sources
);
CREATE TABLE event_impacts (
  event_id bigint NOT NULL REFERENCES events,
  entity_type text NOT NULL CHECK (entity_type IN ('COMPANY','SECTOR','COMMODITY')),
  entity_id bigint NOT NULL,
  direction text NOT NULL CHECK (direction IN ('POSITIVE','NEUTRAL','NEGATIVE')),
  score numeric(4,3) NOT NULL CHECK (score BETWEEN -1 AND 1),
  confidence text NOT NULL CHECK (confidence IN ('HIGH','MEDIUM','LOW')),
  reason text NOT NULL,                     -- wajib: tanpa alasan, tidak disimpan
  inference_kind text NOT NULL DEFAULT 'INFERENCE' CHECK (inference_kind IN ('FACT','INFERENCE')),
  PRIMARY KEY (event_id, entity_type, entity_id)
);

-- ───────── Portfolio & clients (dummy only di repo) ─────────
CREATE TABLE clients (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  client_code text UNIQUE NOT NULL,
  name text NOT NULL,
  client_type text,
  rm_id bigint REFERENCES users,
  risk_profile text,
  aum numeric, cash_balance numeric,
  last_transaction_at timestamptz,
  status text DEFAULT 'ACTIVE',
  is_dummy boolean NOT NULL DEFAULT true    -- guard: produksi menolak is_dummy=false tanpa flag eksplisit
);
CREATE TABLE portfolios (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  owner_user_id bigint REFERENCES users,
  client_id bigint REFERENCES clients,
  name text NOT NULL,
  CHECK ((owner_user_id IS NULL) <> (client_id IS NULL))
);
CREATE TABLE portfolio_positions (
  portfolio_id bigint NOT NULL REFERENCES portfolios,
  security_id bigint NOT NULL REFERENCES securities,
  quantity numeric NOT NULL, avg_cost numeric,
  PRIMARY KEY (portfolio_id, security_id)
);
CREATE TABLE client_transactions (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  client_id bigint NOT NULL REFERENCES clients,
  security_id bigint REFERENCES securities,
  side text CHECK (side IN ('BUY','SELL','DEPOSIT','WITHDRAW')),
  amount numeric NOT NULL, ts timestamptz NOT NULL
);
CREATE TABLE client_opportunities (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  client_id bigint NOT NULL REFERENCES clients,
  opportunity_type text NOT NULL CHECK (opportunity_type IN
    ('REACTIVATION','REBALANCING','BOND','STOCK','MUTUAL_FUND','CASH_DEPLOYMENT')),
  estimated_value numeric, score numeric(5,2),
  reason text NOT NULL, recommended_action text,
  status text NOT NULL DEFAULT 'OPEN',
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ───────── Alerts & AI ─────────
CREATE TABLE alerts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id bigint NOT NULL REFERENCES users,
  entity_type text, entity_id bigint,
  rule jsonb NOT NULL, last_fired_at timestamptz
);
CREATE TABLE ai_conversations (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id bigint NOT NULL REFERENCES users,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE ai_messages (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  conversation_id bigint NOT NULL REFERENCES ai_conversations,
  role text NOT NULL CHECK (role IN ('user','assistant','tool')),
  content jsonb NOT NULL,                   -- termasuk tool_calls + citations
  confidence text CHECK (confidence IN ('HIGH','MEDIUM','LOW')),
  created_at timestamptz NOT NULL DEFAULT now()
);
-- Cache hasil TradingAgents per (ticker, tanggal): satu run mahal, jangan ulang.
CREATE TABLE research_runs (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  company_id bigint NOT NULL REFERENCES companies,
  as_of date NOT NULL,
  engine text NOT NULL DEFAULT 'tradingagents',
  report jsonb NOT NULL,
  llm_model text, cost_usd numeric,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (company_id, as_of, engine)
);

CREATE INDEX news_published_idx ON news (published_at DESC);
CREATE INDEX events_ts_idx ON events (ts DESC);
CREATE INDEX news_entities_entity_idx ON news_entities (entity_type, entity_id);
