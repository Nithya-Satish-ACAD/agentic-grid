# Example Transaction Workflow: Solar Agent Buys Energy

This document traces a single, complete P2P energy transaction, showing how the Gateway and the two autonomous agents interact.

### Scenario

-   The **Solar Agent** starts with a low battery (2.0 kWh out of 15.0 kWh).
-   The **Utility Agent** is online and has ample energy to sell.
-   Both agents have successfully registered with the **Mock Beckn Gateway**.

---

### Step-by-Step Flow

**1. Decision to Buy (Solar Agent)**

-   **Trigger**: The Solar Agent's internal `agent_simulation_loop` runs its 20-second cycle.
-   **Action**: The `supervisor_node` in its LangGraph brain checks its profile. Since `2.0 kWh` is less than the 20% threshold (`3.0 kWh`), it decides to act as a **BAP (Buyer)**.
-   **Result**: The graph's state is updated, and the flow is routed to the `initiate_search` node.

**2. Search Request (Solar Agent → Gateway)**

-   **Trigger**: The `initiate_search` node is executed.
-   **Action**: The node constructs a Beckn `/search` request payload. The agent's `invoke_and_dispatch` function then sends this as an HTTP POST request to the Gateway's `/search` endpoint.
-   **Log (Solar)**: `--- DISPATCHING HTTP POST to http://localhost:9000/search ---`

**3. Broadcast (Gateway → All Sellers)**

-   **Trigger**: The Gateway receives the `/search` request.
-   **Action**: It immediately returns an `ACK` response to the Solar Agent. In the background, it looks up its registry and finds both the Solar and Utility agents are registered as potential sellers. It forwards the original search payload to both of their `/search` endpoints.
-   **Log (Gateway)**: `Gateway forwarding search to http://localhost:8001/search`
-   **Log (Gateway)**: `Gateway forwarding search to http://localhost:8002/search`

**4. Formulating Offers (Utility & Solar Agents)**

-   **Utility Agent (as BPP):**
    -   **Trigger**: It receives the forwarded `/search` request.
    -   **Action**: Its `formulate_offer` node runs. Since it's a utility, it always has energy to sell. It creates an `EnergyOffer` (e.g., for $0.25/kWh) and dispatches it as an `/on_search` callback directly to the Solar Agent's URI (which it knows from the request's `context.bap_uri`).
    -   **Log (Utility)**: `--- BPP (utility-agent-01): FORMULATE OFFER ---`
    -   **Log (Utility)**: `--- DISPATCHING HTTP POST to http://localhost:8001/on_search ---`

-   **Solar Agent (as BPP):**
    -   **Trigger**: It also receives the forwarded `/search` request.
    -   **Action**: Its `formulate_offer` node runs but checks its internal state. Since its battery is low, it correctly decides it has no surplus energy to sell and does nothing.
    -   **Log (Solar)**: `Solar Agent has insufficient surplus energy. Not making an offer.`

**5. Evaluation and Selection (Solar Agent)**

-   **Trigger**: The Solar Agent receives the `/on_search` callback from the Utility Agent.
-   **Action**: The graph is invoked, routing to the `evaluate_offers` node. This node analyzes the list of received offers (in this case, only one) and selects the best one.
-   **Result**: The graph flow proceeds to the `send_select` node.
-   **Log (Solar)**: `Best offer selected: $0.25/kWh from utility-agent-01`

**6. The Select/Confirm Handshake (Peer-to-Peer)**

A rapid, automated negotiation now occurs directly between the two agents:

-   The Solar Agent's `send_select_node` runs, dispatching a `/select` request to the Utility Agent.
-   The Utility Agent receives `/select`, runs `process_selection_node`, and dispatches an `/on_select` back.
-   The Solar Agent receives `/on_select`, runs `send_confirm_node`, and dispatches a final `/confirm` request.
-   The Utility Agent receives `/confirm`, runs `process_confirmation_node`, finalizes the contract, updates its state, and dispatches the final `/on_confirm` callback.

**7. Completion (Solar Agent)**

-   **Trigger**: The Solar Agent receives the final `/on_confirm` callback containing the finalized contract details.
-   **Action**: The graph routes to the `process_bap_completion_node`. This node updates the agent's internal state, increasing its battery level with the purchased energy.
-   **Result**: The transaction is complete.
-   **Log (Solar)**: `✅ Contract confirmed! Energy purchased. New battery level: 12.50 kWh`

The system is now in a new state, and the Solar Agent's next simulation cycle will see that its energy is stable, causing it to remain idle until its battery level crosses a threshold again.