// Tipe aset: label, warna, dan urutan legenda (dipakai peta 2D dan globe 3D).
export const ASSET_TYPES = {
  MINE: { label: "Tambang", color: "#f1c40f" },
  SMELTER: { label: "Smelter / pabrik logam", color: "#2ecc71" },
  PORT: { label: "Pelabuhan / terminal", color: "#3498db" },
  POWER_PLANT: { label: "Pembangkit listrik", color: "#b57edc" },
  GAS_FIELD: { label: "Lapangan migas", color: "#00bcd4" },
  FACTORY: { label: "Pabrik", color: "#e67e22" },
  PLANTATION: { label: "Perkebunan", color: "#8bc34a" },
  TOLL_ROAD: { label: "Jalan tol", color: "#ff7043" },
  AIRPORT: { label: "Bandara", color: "#5c6bc0" },
  BRANCH: { label: "Kantor cabang bank", color: "#ec407a" },
  OFFICE: { label: "Kantor pusat", color: "#cfd8dc" },
};

// Kunci = nama sektor di DB (sectors.name); label ditampilkan ke pengguna.
export const SECTORS = {
  "Basic Materials": { label: "Bahan baku" },
  Energy: { label: "Energi" },
  Financials: { label: "Keuangan" },
  Infrastructures: { label: "Infrastruktur" },
  Industrials: { label: "Industri" },
  "Consumer Non-Cyclicals": { label: "Konsumer primer" },
  Healthcare: { label: "Kesehatan" },
  Technology: { label: "Teknologi" },
  Publik: { label: "Infrastruktur umum" },
};
