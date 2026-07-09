import axios from "axios";

// Endpoints follow the API Contract in PRD.md (source of truth).
const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${baseURL}/api/cellcheck`,
  headers: { "Content-Type": "application/json" },
});

// GET /health
export async function getHealth() {
  const { data } = await api.get("/health");
  return data;
}

// Quick Check — POST /quick
export async function quickCheck(query) {
  const { data } = await api.post("/quick", { query });
  return data;
}

// STR Test Reader — POST /str-analysis
export async function analyzeSTR({ claimedIdentity, strProfile }) {
  const { data } = await api.post("/str-analysis", {
    claimed_identity: claimedIdentity,
    str_profile: strProfile,
  });
  return data;
}

// Methods Section Generator — POST /methods-section
// payload: { cell_line, source, authentication_date, authentication_service,
//            mycoplasma_test_date, passage_range, target_journal }
export async function generateMethods(payload) {
  const { data } = await api.post("/methods-section", payload);
  return data;
}

export default api;
