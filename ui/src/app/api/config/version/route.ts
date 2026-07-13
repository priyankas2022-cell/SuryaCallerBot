import { NextResponse } from "next/server";

import { healthApiV1HealthGet } from "@/client/sdk.gen";
import type { HealthResponse } from "@/client/types.gen";

// Import version from package.json at build time
import packageJson from "../../../../../package.json";

// Internal/local URLs that are not reachable from the browser
const INTERNAL_HOST_RE = /^https?:\/\/(localhost|127\.0\.0\.1|api)(:\d+)?(\/|$)/;

function isInternalUrl(url: string | undefined | null): boolean {
  return !url || INTERNAL_HOST_RE.test(url);
}

export async function GET() {
  const uiVersion = packageJson.version || "dev";

  // Fetch backend version and config from health endpoint
  let apiVersion = "unknown";
  let backendApiEndpoint: string | null = null;
  let deploymentMode = "oss";
  let authProvider = "local";

  try {
    const response = await healthApiV1HealthGet();
    if (response.data) {
      const data = response.data as HealthResponse;
      apiVersion = data.version;
      // Pass through the backend's own endpoint for display purposes
      backendApiEndpoint = data.backend_api_endpoint;
      deploymentMode = data.deployment_mode;
      authProvider = data.auth_provider;
    }
  } catch {
    // Backend might not be reachable during build or in some deployments
    apiVersion = "unavailable";
  }

  // For the API client base URL: prefer the external tunnel URL from the health
  // endpoint (backendApiEndpoint) because it's reachable from browsers, over
  // BACKEND_URL which is typically an internal Docker hostname like http://api:8000.
  // If both are internal, return null so the browser keeps using window.location.origin
  // and routes through the Next.js proxy instead.
  const clientCandidate = !isInternalUrl(backendApiEndpoint) ? backendApiEndpoint : process.env.BACKEND_URL;
  const clientApiBaseUrl = isInternalUrl(clientCandidate) ? null : clientCandidate;

  return NextResponse.json({
    ui: uiVersion,
    api: apiVersion,
    backendApiEndpoint,
    clientApiBaseUrl,
    deploymentMode,
    authProvider,
  });
}
