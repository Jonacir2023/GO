// Configuração para Google Notebooks API
// Substitua YOUR_CLIENT_ID pelo seu Client ID do Google Console

window.GN_CONFIG = {
  // Google OAuth Client ID (obtido em https://console.cloud.google.com/)
  // Exemplo: '1234567890-abc1def2ghi3jkl4mno5pqr6.apps.googleusercontent.com'
  GOOGLE_CLIENT_ID: 'YOUR_CLIENT_ID_HERE',

  // Escopos necessários para Google Notebooks API
  GOOGLE_SCOPES: 'https://www.googleapis.com/auth/notebooks',

  // Edge Function URLs (por Supabase project)
  EDGE_FUNCTIONS: {
    'ivssgstckfcuiyetxdze': 'https://ivssgstckfcuiyetxdze.supabase.co/functions/v1/sync-google-notebooks',
    'lwjbuzubnxnzkofcrhah': 'https://lwjbuzubnxnzkofcrhah.supabase.co/functions/v1/sync-google-notebooks',
  }
};

// Obter URL da Edge Function baseado no projeto atual
function gnGetEdgeFunctionUrl(obraId) {
  // Determinar qual projeto conforme a obra
  const projectId = (obraId === 'ivssgstckfcuiyetxdze')
    ? 'ivssgstckfcuiyetxdze'
    : 'lwjbuzubnxnzkofcrhah';
  return window.GN_CONFIG.EDGE_FUNCTIONS[projectId];
}
