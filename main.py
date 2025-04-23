import os
import json
import time
from datetime import datetime
from rich import print
from supversior import app  
import traceback 
from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
RUN_DIR = r"/home/kaiyuan/lu2025-17-15/Kaiyuan/sp_group/runs"
os.makedirs(RUN_DIR, exist_ok=True)

def get_next_run_id():
    existing = [f for f in os.listdir(RUN_DIR) if f.startswith("run_") and f.endswith(".json")]
    return len(existing) + 1

def serialize(obj):
    """Convert LangChain message or tool object to plain dict if needed."""
    if hasattr(obj, "dict"):
        return obj.dict()
    elif hasattr(obj, "__dict__"):
        return vars(obj)
    else:
        return str(obj)

def save_run(run_id, result, history):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RUN_DIR, f"run_{run_id:03d}_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)

    safe_result = {}
    if result:
        safe_result = {
            k: serialize(v) for k, v in result.items() if k != "messages"
        }

    with open(os.path.join(run_dir, "result.json"), "w", encoding="utf-8") as f:
        json.dump(safe_result, f, indent=2, ensure_ascii=False)

    with open(os.path.join(run_dir, "messages.txt"), "w", encoding="utf-8") as f:
        for i, msg in enumerate(history):
            f.write(f"[{i+1}] Role: {getattr(msg, 'type', 'unknown')}\n")
            if hasattr(msg, 'name'):
                f.write(f"Name: {getattr(msg, 'name', '')}\n")
            if hasattr(msg, 'tool_call_id'):
                f.write(f"ToolCallID: {getattr(msg, 'tool_call_id')}\n")
            f.write(f"Content:\n{getattr(msg, 'content', str(msg))}\n")
            f.write("=" * 40 + "\n")

def main():
    print("[bold cyan]🚀 GIS Multi-Agent System Ready. Type your task below.")
    print("Type [yellow]'reset'[/yellow] to start a new session, or [yellow]'exit'[/yellow] to quit.")

    state = {}

    while True:
        user_input = input("\n[User] > ").strip()

        if not user_input:
            print("[red]⚠️ Input is empty. Please enter a task description.[/red]")
            continue

        if user_input.lower() in ["exit", "quit", "q"]:
            print("[bold red]\n👋 Exiting. All sessions saved under /runs/")
            break

        elif user_input.lower() == "reset":
            print("\n🧼 [blue]Session reset. Ready for a new query.[/blue]")
            state.clear()
            continue

        run_id = get_next_run_id()
        print(f"\n🧠 [green]Running Agent Workflow (Session #{run_id})...[/green]")

        
        result = None
        history = []
        start = time.time()

        try:
            print("🚀 Invoking LangGraph agent...\n")

            stream = app.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config={"configurable": {"thread_id": str(run_id)}}
            )

            start = time.time()
            result = None

            for i, step in enumerate(stream):
                print(f"\n[bold cyan]🔁 Step {i + 1}[/bold cyan]")
                print(f"[dim][DEBUG] Step keys: {list(step.keys())}[/dim]")

                for agent_name, agent_output in step.items():
                    print(f"[bold magenta]🧠 Agent: {agent_name}[/bold magenta]")

                    messages = agent_output.get("messages", [])
                    history.extend(messages)  

                    for msg in messages:
                        if isinstance(msg, HumanMessage):
                            print(f"[green]👤 [User]: {msg.content}[/green]")

                        elif isinstance(msg, AIMessage):
                            print(f"[blue]🤖 {agent_name}: {msg.content or '[No content]'}[/blue]")
                            for call in msg.tool_calls or []:
                                tool_name = call.get("function", {}).get("name", "unknown")
                                tool_args = call.get("function", {}).get("arguments", "")
                                tool_id = call.get("id", "unknown")
                                print(f"[yellow]  🔧 Tool Call -> {tool_name}({tool_args}) [id: {tool_id}][/yellow]")

                        elif isinstance(msg, ToolMessage):
                            tool_id = getattr(msg, "tool_call_id", "unknown")
                            print(f"[magenta]🛠️ [Tool Result {tool_id}]: {msg.content}[/magenta]")

                        else:
                            msg_type = type(msg).__name__
                            content = getattr(msg, "content", str(msg))
                            print(f"[dim]🔹 [{msg_type}]: {content}[/dim]")

                result = step  

            end = time.time()
            print(f"\n✅ [bold green]Execution complete in {end - start:.2f}s[/bold green]")

            tool_agents = {
                getattr(msg, "name", None)
                for msg in history
                if getattr(msg, "type", "") == "tool"
            }
            if tool_agents:
                print(f"🧩 Agents invoked: [bold yellow]{', '.join(sorted(tool_agents))}[/bold yellow]")

            if any("stderr" in getattr(msg, "content", "").lower() for msg in history):
                print("⚠️  [red]stderr detected in tool execution. Review output.[/red]")

        except Exception as e:
            print("\n❌ [bold red]Error during execution[/bold red]")
            traceback.print_exc()
            print("\n🛠️ Last known agent state before crash:\n")
            if result and isinstance(result, dict):
                for agent_name, agent_output in result.items():
                    print(f"🔸 Agent: {agent_name}")
                    for msg in agent_output.get("messages", []):
                        role = getattr(msg, "type", "unknown")
                        print(f"  🔹 {role.capitalize()}: {getattr(msg, 'content', str(msg))[:100]}")

        finally:
            save_run(run_id, result, history)

            end = time.time() if 'end' in locals() else time.time()
            print(f"\n✅ Execution complete in {end - start:.2f}s")



        

if __name__ == "__main__":
    main()
