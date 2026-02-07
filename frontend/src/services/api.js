import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const getPairs = async (limit = 100, offset = 0) => {
  const response = await axios.get(`${API_BASE}/pairs`, {
    params: { limit, offset }
  });
  return response.data;
};

export const getPair = async (pairId) => {
  const response = await axios.get(`${API_BASE}/pairs/${pairId}`);
  return response.data;
};

export const getTriplets = async () => {
  const response = await axios.get(`${API_BASE}/triplets`);
  return response.data;
};
