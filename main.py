from agent.graph.agent_graph import build_agent_graph
import readline
import traceback

output_dir = "/home/kaiyuan/Downloads/agent_output"
agent_graph = build_agent_graph()

print("\n👋 Welcome to GeoAgent! Please enter your geographic data processing queries.")
print("Type 'new' to start a new session, or 'exit' to quit.\n")

session_id = None

while True:
    query = input("🌍 Enter your query >>> ").strip()

    if query.lower() == "exit":
        print("👋 Goodbye!")
        break
    elif query.lower() == "new":
        session_id = None
        print("🆕 New session started.")
        continue

    session_id = session_id or f"session_{hash(query) % 1_000_000}"
    initial_state = {
        "question": query,
        "output_path": output_dir,
        "history": []
    }

    print("\n🚀 Starting agent pipeline...")
    print("🧾 Initial State:", initial_state)

    try:
        result = None
        events = agent_graph.stream(initial_state, config={"checkpoint_id": session_id, "debug": True})
        for step in events:
            if not isinstance(step, dict):
                print("⚠️ Unexpected step type:", type(step), step)
                continue

            for node_name, node_value in step.items():
                print(f"\n🔁 [step: {node_name}]")

                if node_name in {"file_search", "rag_context"}:
                    print(node_value)
                    continue

                if node_name == "code_runner" and isinstance(node_value, dict):
                    output = node_value 
                    history = output.get("history", [])
                    print(f"\n🧪 Code Generation Attempts: {len(history)}\n")
                    for i, attempt in enumerate(history, 1):
                        print(f"--- Attempt {i} ---")
                        print("📝 Code Snippet:\n", attempt["code"] or "(empty)")
                        print("📤 STDOUT:\n", attempt["stdout"])
                        print("📛 STDERR:\n", attempt["stderr"])
                        print("❌ Error:\n", attempt["error"])
                    final = output.get("success")
                    if final:
                        print("✅ Final code execution succeeded!")
                    else:
                        print("⚠️ All attempts failed.")

                    for k, v in node_value.items():
                        if k == "context" or k == "history":
                            continue
                        print(f"{k}:\n{v}\n")
                
                if node_name == "execution_result":
                    result = node_value

                # fallback print other nodes
                print(node_value)

        print("\n🎯 Final Result:")
        print(result or "⚠️ No final result returned.")

    except Exception as e:
        import traceback
        print("🔥 [bold red]Unhandled Exception during agent execution:[/bold red]")
        traceback.print_exc()


        




