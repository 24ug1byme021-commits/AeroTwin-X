/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend base URL for a production deployment, e.g. https://aerotwinx-backend.onrender.com.
   *  Leave unset for local dev — the Vite proxy in vite.config.ts handles it instead. */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
