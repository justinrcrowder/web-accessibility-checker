import { Container, getContainer } from "@cloudflare/containers";

/**
 * Durable Object that owns a single instance of the Flask auditor container.
 * The Container base class handles starting the image, health checks, and
 * proxying HTTP requests to `defaultPort`.
 */
export class AuditorContainer extends Container {
  // Must match EXPOSE / gunicorn bind port in the Dockerfile.
  defaultPort = 8080;
  // Stop the container after 10 minutes idle to avoid paying for idle compute.
  sleepAfter = "10m";

  override onError(error: unknown) {
    console.log("Container error:", error);
  }
}

interface Env {
  AUDITOR: DurableObjectNamespace<AuditorContainer>;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Route all traffic to a single shared container instance.
    const container = getContainer(env.AUDITOR);
    return container.fetch(request);
  },
};
