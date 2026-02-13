import { useCallback, useState } from "react";

import { QUERY_PATH } from "../config/api";
import type { QueryRequest, QueryResponse } from "../types/query";

export type QueryStatus = "idle" | "loading" | "success" | "error";

export type QueryState = {
  status: QueryStatus;
  data: QueryResponse | null;
  error: string | null;
};

const initialState: QueryState = {
  status: "idle",
  data: null,
  error: null,
};

export function useQuery(apiBase: string) {
  const [state, setState] = useState<QueryState>(initialState);

  const runQuery = useCallback(
    async (payload: QueryRequest) => {
      setState({ status: "loading", data: null, error: null });

      try {
        const response = await fetch(`${apiBase}${QUERY_PATH}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const message = await response.text();
          throw new Error(message || `Request failed (${response.status}).`);
        }

        const data = (await response.json()) as QueryResponse;
        setState({ status: "success", data, error: null });
        return data;
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Unexpected error";
        setState({ status: "error", data: null, error: message });
        return null;
      }
    },
    [apiBase]
  );

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return { state, runQuery, reset };
}
