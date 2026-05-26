import type { OpenNextConfig } from "@opennextjs/cloudflare";

// @opennextjs/cloudflare compiles the Next.js App Router to run on
// Cloudflare Workers. With nodejs_compat in wrangler.toml, standard
// Node.js APIs (crypto, stream, buffer) are available in every route —
// no per-route `export const runtime = 'edge'` needed.
const config: OpenNextConfig = {
  default: {
    override: {
      wrapper: "cloudflare-node",    // uses Node.js compat runtime
      converter: "edge",
    },
  },
  middleware: {
    external: true,
    override: {
      wrapper: "cloudflare-edge",
      converter: "edge",
      proxyExternalRequest: "fetch",
    },
  },
};

export default config;
