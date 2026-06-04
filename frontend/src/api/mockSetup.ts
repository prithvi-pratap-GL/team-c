import { mockLogin, mockChat, mockListDocuments, mockIngest } from "./mock";

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Override fetch to intercept API calls
const originalFetch = window.fetch;

window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const url = typeof input === "string" ? input : input.toString();

  // Only intercept API calls
  if (!url.includes("/api/v1/")) {
    return originalFetch(input, init);
  }

  console.log("[Mock API]", init?.method || "GET", url);

  try {
    let data: any = null;

    // Login endpoint
    if (url.includes("/auth/login")) {
      await delay(800);
      const body = JSON.parse(init?.body as string);
      data = mockLogin(body.username, body.password);
    }
    // Chat endpoint
    else if (url.includes("/chat")) {
      await delay(1500);
      const body = JSON.parse(init?.body as string);
      data = mockChat(body.query);
    }
    // Documents endpoint
    else if (url.includes("/documents")) {
      await delay(600);
      const params = new URL(url).searchParams;
      data = mockListDocuments(params.get("department") || undefined);
    }
    // Ingest endpoint
    else if (url.includes("/ingest")) {
      await delay(2000);
      data = mockIngest();
    }
    // Feedback endpoint
    else if (url.includes("/feedback")) {
      await delay(500);
      data = { status: "success" };
    }
    // Unknown endpoint - return 404
    else {
      return new Response(
        JSON.stringify({ detail: "Endpoint not mocked" }),
        { status: 404, headers: { "Content-Type": "application/json" } }
      );
    }

    // Return successful response
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Mock request failed";
    console.error("[Mock API Error]", message);

    return new Response(JSON.stringify({ detail: message }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }
};

console.log("[Mock API] Interceptor activated - all API calls will use mock data");
