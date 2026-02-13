import { useCallback, useState } from "react";

import { queryAgent } from "../config/api";
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

export function useQuery() {
  const [state, setState] = useState<QueryState>(initialState);

  const runQuery = useCallback(
    async (payload: QueryRequest) => {
      setState({ status: "loading", data: null, error: null });

      try {
        const data = (await queryAgent(payload)) as QueryResponse;
        setState({ status: "success", data, error: null });
        return data;
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Unexpected error";
        setState({ status: "error", data: null, error: message });
        return null;
      }
    },
    []
  );

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return { state, runQuery, reset };
}
