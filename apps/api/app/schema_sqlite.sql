-- Subset dev-only dari docs/01-schema.sql untuk SQLite (tanpa PostGIS; lat/lng biasa). Produksi tetap PostgreSQL.
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('ADMIN','ANALYST','RM','INVESTOR')));
CREATE TABLE IF NOT EXISTS data_sources (
  id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, provider TEXT NOT NULL, source_type TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sectors (id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS commodities (id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY, ticker TEXT UNIQUE, name TEXT NOT NULL, sector_id INTEGER REFERENCES sectors,
  description TEXT, is_listed INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS company_commodities (company_id INTEGER NOT NULL REFERENCES companies, commodity TEXT NOT NULL,
  PRIMARY KEY (company_id, commodity));
CREATE TABLE IF NOT EXISTS prices (
  company_id INTEGER NOT NULL REFERENCES companies, ts TEXT NOT NULL, close REAL NOT NULL, volume INTEGER,
  source_id INTEGER NOT NULL REFERENCES data_sources, PRIMARY KEY (company_id, ts));
CREATE TABLE IF NOT EXISTS fundamentals (
  company_id INTEGER NOT NULL REFERENCES companies, period TEXT NOT NULL, revenue REAL, ebitda REAL, net_income REAL,
  roe REAL, market_cap REAL, pe REAL, pbv REAL, dividend_yield REAL, as_of TEXT,
  source_id INTEGER NOT NULL REFERENCES data_sources, PRIMARY KEY (company_id, period));
CREATE TABLE IF NOT EXISTS news (
  id INTEGER PRIMARY KEY, title TEXT NOT NULL, url TEXT UNIQUE NOT NULL, publisher TEXT, published_at TEXT NOT NULL,
  sentiment TEXT, source_id INTEGER REFERENCES data_sources);
CREATE TABLE IF NOT EXISTS news_entities (news_id INTEGER NOT NULL REFERENCES news, entity_type TEXT NOT NULL,
  entity_id INTEGER NOT NULL, PRIMARY KEY (news_id, entity_type, entity_id));
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY, news_id INTEGER UNIQUE REFERENCES news,  -- news_id: khusus dev, satu event per berita
  event_type TEXT NOT NULL, title TEXT NOT NULL, ts TEXT NOT NULL, confidence TEXT);
CREATE TABLE IF NOT EXISTS event_impacts (
  event_id INTEGER NOT NULL REFERENCES events, entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL,
  direction TEXT NOT NULL, score REAL NOT NULL CHECK (score BETWEEN -1 AND 1), confidence TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (length(reason) > 0), PRIMARY KEY (event_id, entity_type, entity_id));
CREATE TABLE IF NOT EXISTS market_quotes (
  code TEXT PRIMARY KEY, name TEXT NOT NULL, value REAL NOT NULL, change_pct REAL NOT NULL,
  as_of TEXT NOT NULL, source_id INTEGER NOT NULL REFERENCES data_sources);
CREATE TABLE IF NOT EXISTS locations (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, location_type TEXT NOT NULL, lat REAL NOT NULL, lng REAL NOT NULL,
  province TEXT, source_id INTEGER NOT NULL REFERENCES data_sources, verified_at TEXT);  -- NULL = belum diverifikasi
CREATE TABLE IF NOT EXISTS assets (
  id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies, asset_type TEXT NOT NULL, name TEXT NOT NULL,
  location_id INTEGER NOT NULL REFERENCES locations, commodity TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY, client_code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, rm_id INTEGER REFERENCES users,
  risk_profile TEXT, aum REAL NOT NULL, cash_balance REAL NOT NULL, last_transaction_at TEXT,
  is_dummy INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS positions (  -- tepat satu pemilik: user (portofolio sendiri) atau client
  user_id INTEGER REFERENCES users, client_id INTEGER REFERENCES clients,
  company_id INTEGER NOT NULL REFERENCES companies, quantity REAL NOT NULL, avg_cost REAL,
  CHECK ((user_id IS NULL) <> (client_id IS NULL)));
CREATE TABLE IF NOT EXISTS watchlist (
  user_id INTEGER NOT NULL REFERENCES users, company_id INTEGER NOT NULL REFERENCES companies, PRIMARY KEY (user_id, company_id));
CREATE TABLE IF NOT EXISTS research_runs (
  company_id INTEGER NOT NULL REFERENCES companies, as_of TEXT NOT NULL, status TEXT NOT NULL,
  report TEXT, error TEXT, PRIMARY KEY (company_id, as_of));
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY, ts TEXT NOT NULL DEFAULT (datetime('now')), user_id INTEGER, action TEXT NOT NULL, target TEXT);
