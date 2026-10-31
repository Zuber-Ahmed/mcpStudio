import createClient, { type ClientOptions } from "openapi-fetch";
import type { paths as ControlPaths } from "./generated/control-api";
import type { paths as BootstrapPaths } from "./generated/bootstrap-api";

// Callers choose the local base URL and authentication transport explicitly.
// This factory does not implement session bootstrap, CSRF policy or authorization.
type Options = ClientOptions & { baseUrl: string };

export const createControlClient = (options: Options) =>
  createClient<ControlPaths>(options);

export const createBootstrapClient = (options: Options) =>
  createClient<BootstrapPaths>(options);
