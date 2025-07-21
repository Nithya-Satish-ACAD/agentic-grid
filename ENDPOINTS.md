# API Endpoints Documentation

This document outlines the API endpoints for each service in the P2P Energy Grid Simulation.

## 1. Mock Beckn Gateway

**Base URL:** `http://localhost:9000`

### `POST /register`

Registers a Beckn Provider Platform (BPP) so that it can be discovered. Agents acting as sellers call this on startup.

-   **Request Body:**
    ```json
    {
      "bpp_uri": "[http://agent-url.com](http://agent-url.com)"
    }
    ```
-   **Response:**
    ```json
    {
      "status": "success"
    }
    ```

### `POST /search`

Receives a search request from a Beckn Application Platform (BAP) and broadcasts it to all registered BPPs in the background.

-   **Request Body:** A standard Beckn search payload.
    ```json
    {
      "context": {
        "domain": "ONIX:energy",
        "action": "search",
        "version": "1.0.0",
        "bap_id": "solar-agent-01",
        "bap_uri": "http://localhost:8001",
        "transaction_id": "some-unique-id",
        // ... other context fields
      },
      "message": {
        "intent": {}
      }
    }
    ```
-   **Response:** An immediate Beckn Acknowledgement.
    ```json
    {
      "message": {
        "ack": {
          "status": "ACK"
        }
      }
    }
    ```

---

## 2. Solar Agent & Utility Agent

**Base URLs:**
-   Solar Agent: `http://localhost:8001`
-   Utility Agent: `http://localhost:8002`

Both agents use a single, dynamic endpoint to handle all incoming Beckn protocol actions. This simplifies the server logic and aligns with the Beckn specification.

### `POST /{action:path}`

This single endpoint handles all Beckn transaction messages. The `action` in the URL path corresponds to the `context.action` field in a Beckn request, but is handled dynamically for simplicity in this simulation.

#### Role: Agent as a BPP (Seller)

An agent acts as a BPP when it receives these requests:

-   **`POST /search`**: Receives a forwarded search request from the Gateway. Triggers the `formulate_offer` logic.
-   **`POST /select`**: Receives a selection confirmation from a BAP. Triggers the `process_selection` logic.
-   **`POST /confirm`**: Receives the final order confirmation from a BAP. Triggers the `process_confirmation` logic.

#### Role: Agent as a BAP (Buyer)

An agent acts as a BAP when it receives these callback requests:

-   **`POST /on_search`**: Receives a catalog of offers from a BPP. Triggers the `evaluate_offers` logic.
-   **`POST /on_select`**: Receives confirmation that its selection was received. Triggers the `send_confirm` logic.
-   **`POST /on_confirm`**: Receives the finalized contract from the BPP. Triggers the `process_bap_completion` logic.

All requests to this endpoint expect a standard Beckn JSON payload and will return a standard Beckn `ACK` response immediately, while processing the logic in a background task.