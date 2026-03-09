import { useState, useCallback, useRef } from "react";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
  Panel,
} from "reactflow";
import "reactflow/dist/style.css";

const C = {
  bg: "#0d1117",
  surface: "#161b22",
  surfaceHover: "#1c2128",
  border: "#30363d",
  borderActive: "#f0b429",
  text: "#e6edf3",
  textMuted: "#7d8590",
  amber: "#f0b429",
  amberDim: "#f0b42920",
  green: "#3fb950",
  blue: "#58a6ff",
  purple: "#bc8cff",
  red: "#ff7b72",
  cyan: "#39c5cf",
};

const NODE_TYPES_META = {
  input:      { label: "Input",      color: C.green,  icon: "⬇", desc: "Entry point — receives the user message" },
  llm_call:   { label: "LLM Call",   color: C.blue,   icon: "◈", desc: "Calls the language model with a system prompt" },
  tool_call:  { label: "Tool Call",  color: C.purple, icon: "⚙", desc: "Executes an external tool or API" },
  conditional:{ label: "Conditional",color: C.amber,  icon: "⟨⟩", desc: "Routes based on a condition" },
  output:     { label: "Output",     color: C.red,    icon: "⬆", desc: "Returns the final response" },
};

function AgentNode({ data, selected }) {
  const meta = NODE_TYPES_META[data.type] || NODE_TYPES_META.llm_call;
  return (
    <div style={{
      background: selected ? C.surfaceHover : C.surface,
      border: `1.5px solid ${selected ? meta.color : C.border}`,
      borderRadius: 8,
      minWidth: 180,
      boxShadow: selected ? `0 0 0 3px ${meta.color}22, 0 4px 24px #00000060` : "0 2px 8px #00000040",
      transition: "all 0.15s ease",
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    }}>
      <div style={{
        display: "flex", alignItems: "center", gap: 8,
        padding: "8px 12px",
        borderBottom: `1px solid ${C.border}`,
        borderRadius: "6px 6px 0 0",
        background: `${meta.color}14`,
      }}>
        <span style={{ fontSize: 14, color: meta.color }}>{meta.icon}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color: meta.color, letterSpacing: "0.08em", textTransform: "uppercase" }}>
          {meta.label}
        </span>
      </div>
      <div style={{ padding: "8px 12px" }}>
        <div style={{ fontSize: 12, color: C.text, fontWeight: 600, marginBottom: 2 }}>
          {data.label}
        </div>
        {data.model && (
          <div style={{ fontSize: 10, color: C.textMuted }}>{data.model}</div>
        )}
        {data.tools && data.tools.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 3, marginTop: 4 }}>
            {data.tools.map(t => (
              <span key={t} style={{
                fontSize: 9, padding: "1px 5px", borderRadius: 3,
                background: `${C.purple}20`, color: C.purple, border: `1px solid ${C.purple}40`
              }}>{t}</span>
            ))}
          </div>
        )}
      </div>
      {data.type !== "input" && (
        <Handle type="target" position={Position.Left} style={{
          background: meta.color, border: `2px solid ${C.bg}`, width: 10, height: 10, left: -5
        }} />
      )}
      {data.type !== "output" && (
        <Handle type="source" position={Position.Right} style={{
          background: meta.color, border: `2px solid ${C.bg}`, width: 10, height: 10, right: -5
        }} />
      )}
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

const defaultNodes = [
  { id: "1", type: "agentNode", position: { x: 80, y: 200 },
    data: { type: "input", label: "User Message" } },
  { id: "2", type: "agentNode", position: { x: 320, y: 160 },
    data: { type: "llm_call", label: "intake_agent", model: "gpt-4o",
      tools: ["verify_insurance", "check_availability"], systemPrompt: "You are a HIPAA-compliant patient intake assistant.\nCollect name, DOB, reason for visit, and insurance ID." } },
  { id: "3", type: "agentNode", position: { x: 320, y: 320 },
    data: { type: "tool_call", label: "tools", tools: ["schedule_appointment"] } },
  { id: "4", type: "agentNode", position: { x: 580, y: 200 },
    data: { type: "output", label: "Response" } },
];

const defaultEdges = [
  { id: "e1-2", source: "1", target: "2", animated: true, style: { stroke: C.green, strokeWidth: 1.5 } },
  { id: "e2-3", source: "2", target: "3", animated: true, style: { stroke: C.blue, strokeWidth: 1.5 }, label: "has tools", labelStyle: { fill: C.textMuted, fontSize: 10 }, labelBgStyle: { fill: C.bg } },
  { id: "e3-2", source: "3", target: "2", animated: true, style: { stroke: C.purple, strokeWidth: 1.5, strokeDasharray: "4 2" } },
  { id: "e2-4", source: "2", target: "4", animated: true, style: { stroke: C.red, strokeWidth: 1.5 }, label: "done", labelStyle: { fill: C.textMuted, fontSize: 10 }, labelBgStyle: { fill: C.bg } },
];

function generateYAML(agentName, agentVersion, nodes, edges) {
  const llmNodes = nodes.filter(n => n.data.type === "llm_call");
  const toolNodes = nodes.filter(n => n.data.type === "tool_call");
  const allTools = [...new Set([
    ...llmNodes.flatMap(n => n.data.tools || []),
    ...toolNodes.flatMap(n => n.data.tools || []),
  ])];

  const edgeLines = edges.map(e => {
    const src = nodes.find(n => n.id === e.source)?.data.label || e.source;
    const tgt = nodes.find(n => n.id === e.target)?.data.label || e.target;
    return `  - from: ${src === "User Message" ? "__start__" : src}\n    to: ${tgt === "Response" ? "__end__" : tgt}`;
  }).join("\n");

  const nodeLines = llmNodes.map(n => {
    const toolList = (n.data.tools || []).map(t => `    - ${t}`).join("\n");
    const prompt = (n.data.systemPrompt || "You are a helpful assistant.").replace(/\n/g, "\n      ");
    return `  - id: ${n.data.label}
    type: llm_call
    system_prompt: |
      ${prompt}${toolList ? `\n    tools:\n${toolList}` : ""}`;
  }).join("\n");

  const toolLines = allTools.map(t => `  - name: ${t}
    description: ${t.replace(/_/g, " ")}
    parameters:
      - name: input
        type: string
        required: true`).join("\n");

  return `name: ${agentName.toLowerCase().replace(/\s+/g, "_")}
version: "${agentVersion}"
description: Generated by AgentPort canvas

llm:
  provider: openai
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
  temperature: 0.2
  max_tokens: 1024

nodes:
${nodeLines}

edges:
${edgeLines}

tools:
${toolLines}

compliance:
  frameworks: [HIPAA, SOC2]
  audit_logging: true
  data_residency: customer_infrastructure
`;
}

export default function AgentPortCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState(defaultNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(defaultEdges);
  const [selectedNode, setSelectedNode] = useState(null);
  const [agentName, setAgentName] = useState("patient_intake");
  const [agentVersion, setAgentVersion] = useState("1.0.0");
  const [yamlOutput, setYamlOutput] = useState(null);
  const [copied, setCopied] = useState(false);
  const idCounter = useRef(10);

  const onConnect = useCallback((params) =>
    setEdges(eds => addEdge({ ...params, animated: true, style: { stroke: C.blue, strokeWidth: 1.5 } }, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((_, node) => setSelectedNode(node), []);
  const onPaneClick = useCallback(() => setSelectedNode(null), []);

  const addNode = (type) => {
    const id = String(++idCounter.current);
    setNodes(nds => [...nds, {
      id, type: "agentNode",
      position: { x: 200 + Math.random() * 200, y: 150 + Math.random() * 200 },
      data: { type, label: `${type}_${id}`, tools: [], model: type === "llm_call" ? "gpt-4o" : undefined }
    }]);
  };

  const updateSelectedNode = (key, value) => {
    if (!selectedNode) return;
    setNodes(nds => nds.map(n => n.id === selectedNode.id
      ? { ...n, data: { ...n.data, [key]: value } }
      : n
    ));
    setSelectedNode(s => ({ ...s, data: { ...s.data, [key]: value } }));
  };

  const deleteSelectedNode = () => {
    if (!selectedNode) return;
    setNodes(nds => nds.filter(n => n.id !== selectedNode.id));
    setEdges(eds => eds.filter(e => e.source !== selectedNode.id && e.target !== selectedNode.id));
    setSelectedNode(null);
  };

  const exportYAML = () => setYamlOutput(generateYAML(agentName, agentVersion, nodes, edges));

  const copyYAML = () => {
    navigator.clipboard.writeText(yamlOutput);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const sel = selectedNode;
  const selMeta = sel ? NODE_TYPES_META[sel.data.type] : null;

  return (
    <div style={{ width: "100vw", height: "100vh", background: C.bg, display: "flex", flexDirection: "column", fontFamily: "'JetBrains Mono', monospace", color: C.text }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "0 20px", height: 52, borderBottom: `1px solid ${C.border}`, background: C.surface, flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 16, color: C.amber }}>◈</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: C.amber, letterSpacing: "0.1em" }}>AGENTPORT</span>
        </div>
        <div style={{ width: 1, height: 20, background: C.border }} />
        <input value={agentName} onChange={e => setAgentName(e.target.value)}
          style={{ background: "transparent", border: "none", color: C.text, fontSize: 13, fontFamily: "inherit", outline: "none", width: 160 }} />
        <span style={{ color: C.textMuted, fontSize: 12 }}>v</span>
        <input value={agentVersion} onChange={e => setAgentVersion(e.target.value)}
          style={{ background: "transparent", border: "none", color: C.textMuted, fontSize: 12, fontFamily: "inherit", outline: "none", width: 40 }} />
        <div style={{ flex: 1 }} />
        <button onClick={exportYAML} style={{
          background: C.amberDim, border: `1px solid ${C.amber}`, color: C.amber,
          padding: "5px 14px", borderRadius: 5, fontSize: 11, fontWeight: 700,
          letterSpacing: "0.08em", cursor: "pointer", fontFamily: "inherit",
        }}>EXPORT YAML</button>
      </div>

      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        <div style={{ width: 200, borderRight: `1px solid ${C.border}`, background: C.surface, padding: 16, flexShrink: 0, overflowY: "auto" }}>
          <div style={{ fontSize: 9, letterSpacing: "0.12em", color: C.textMuted, marginBottom: 12, textTransform: "uppercase" }}>Node Types</div>
          {Object.entries(NODE_TYPES_META).map(([type, meta]) => (
            <div key={type} onClick={() => addNode(type)} style={{
              display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", borderRadius: 6, marginBottom: 4,
              border: `1px solid ${C.border}`, cursor: "pointer", transition: "all 0.12s", background: "transparent",
            }}
              onMouseEnter={e => { e.currentTarget.style.background = `${meta.color}12`; e.currentTarget.style.borderColor = `${meta.color}60`; }}
              onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.borderColor = C.border; }}
            >
              <span style={{ fontSize: 14, color: meta.color }}>{meta.icon}</span>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: meta.color }}>{meta.label}</div>
                <div style={{ fontSize: 9, color: C.textMuted, marginTop: 1, lineHeight: 1.3 }}>{meta.desc}</div>
              </div>
            </div>
          ))}
          <div style={{ marginTop: 20, padding: 10, borderRadius: 6, background: `${C.amber}08`, border: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 9, color: C.textMuted, lineHeight: 1.5 }}>
              Click a node type to add it to the canvas. Drag to reposition. Connect by dragging from a handle.
            </div>
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <ReactFlow
            nodes={nodes} edges={edges}
            onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
            onConnect={onConnect} onNodeClick={onNodeClick} onPaneClick={onPaneClick}
            nodeTypes={nodeTypes} fitView style={{ background: C.bg }}
          >
            <Background color={C.border} gap={24} size={1} />
            <Controls style={{ background: C.surface, border: `1px solid ${C.border}` }} />
            <MiniMap style={{ background: C.surface, border: `1px solid ${C.border}` }} nodeColor={n => NODE_TYPES_META[n.data?.type]?.color || C.blue} />
            <Panel position="bottom-center">
              <div style={{ fontSize: 10, color: C.textMuted, background: C.surface, padding: "3px 10px", borderRadius: 4, border: `1px solid ${C.border}` }}>
                {nodes.length} nodes · {edges.length} edges
              </div>
            </Panel>
          </ReactFlow>
        </div>

        <div style={{ width: 260, borderLeft: `1px solid ${C.border}`, background: C.surface, padding: 16, flexShrink: 0, overflowY: "auto" }}>
          {!sel ? (
            <div>
              <div style={{ fontSize: 9, letterSpacing: "0.12em", color: C.textMuted, marginBottom: 12, textTransform: "uppercase" }}>Properties</div>
              <div style={{ fontSize: 11, color: C.textMuted, lineHeight: 1.6 }}>Select a node to edit its properties.</div>
            </div>
          ) : (
            <div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                <div style={{ fontSize: 9, letterSpacing: "0.12em", color: selMeta.color, textTransform: "uppercase" }}>{selMeta.label}</div>
                <button onClick={deleteSelectedNode} style={{
                  background: "transparent", border: `1px solid ${C.red}40`, color: C.red,
                  padding: "2px 8px", borderRadius: 4, fontSize: 9, cursor: "pointer", fontFamily: "inherit"
                }}>DELETE</button>
              </div>
              <label style={{ display: "block", marginBottom: 12 }}>
                <div style={{ fontSize: 9, color: C.textMuted, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>Node ID</div>
                <input value={sel.data.label} onChange={e => updateSelectedNode("label", e.target.value)}
                  style={{ width: "100%", background: C.bg, border: `1px solid ${C.border}`, color: C.text, padding: "6px 8px", borderRadius: 4, fontSize: 11, fontFamily: "inherit", boxSizing: "border-box" }} />
              </label>
              {sel.data.type === "llm_call" && (
                <>
                  <label style={{ display: "block", marginBottom: 12 }}>
                    <div style={{ fontSize: 9, color: C.textMuted, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>Model</div>
                    <select value={sel.data.model || "gpt-4o"} onChange={e => updateSelectedNode("model", e.target.value)}
                      style={{ width: "100%", background: C.bg, border: `1px solid ${C.border}`, color: C.text, padding: "6px 8px", borderRadius: 4, fontSize: 11, fontFamily: "inherit" }}>
                      <option>gpt-4o</option>
                      <option>gpt-4o-mini</option>
                      <option>claude-opus-4-6</option>
                      <option>claude-sonnet-4-6</option>
                    </select>
                  </label>
                  <label style={{ display: "block", marginBottom: 12 }}>
                    <div style={{ fontSize: 9, color: C.textMuted, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>System Prompt</div>
                    <textarea value={sel.data.systemPrompt || ""} onChange={e => updateSelectedNode("systemPrompt", e.target.value)} rows={6}
                      style={{ width: "100%", background: C.bg, border: `1px solid ${C.border}`, color: C.text, padding: "6px 8px", borderRadius: 4, fontSize: 10, fontFamily: "inherit", resize: "vertical", lineHeight: 1.5, boxSizing: "border-box" }} />
                  </label>
                </>
              )}
              {(sel.data.type === "llm_call" || sel.data.type === "tool_call") && (
                <label style={{ display: "block", marginBottom: 12 }}>
                  <div style={{ fontSize: 9, color: C.textMuted, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>Tools (comma separated)</div>
                  <input
                    value={(sel.data.tools || []).join(", ")}
                    onChange={e => updateSelectedNode("tools", e.target.value.split(",").map(t => t.trim()).filter(Boolean))}
                    style={{ width: "100%", background: C.bg, border: `1px solid ${C.border}`, color: C.text, padding: "6px 8px", borderRadius: 4, fontSize: 11, fontFamily: "inherit", boxSizing: "border-box" }}
                    placeholder="tool_name, another_tool"
                  />
                </label>
              )}
              <div style={{ marginTop: 8, padding: 10, borderRadius: 6, background: `${selMeta.color}08`, border: `1px solid ${selMeta.color}30` }}>
                <div style={{ fontSize: 9, color: C.textMuted, lineHeight: 1.5 }}>Node ID: <span style={{ color: C.text }}>{sel.id}</span></div>
                <div style={{ fontSize: 9, color: C.textMuted, lineHeight: 1.5, marginTop: 2 }}>Type: <span style={{ color: selMeta.color }}>{sel.data.type}</span></div>
              </div>
            </div>
          )}
        </div>
      </div>

      {yamlOutput && (
        <div style={{ position: "fixed", inset: 0, background: "#00000090", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
          onClick={() => setYamlOutput(null)}>
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, width: 640, maxHeight: "80vh", display: "flex", flexDirection: "column", boxShadow: "0 24px 80px #000000a0" }}
            onClick={e => e.stopPropagation()}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 20px", borderBottom: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: C.amber, letterSpacing: "0.08em" }}>EXPORTED YAML</div>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={copyYAML} style={{ background: C.amberDim, border: `1px solid ${C.amber}`, color: C.amber, padding: "4px 12px", borderRadius: 4, fontSize: 10, cursor: "pointer", fontFamily: "inherit", fontWeight: 700 }}>
                  {copied ? "COPIED ✓" : "COPY"}
                </button>
                <button onClick={() => setYamlOutput(null)} style={{ background: "transparent", border: `1px solid ${C.border}`, color: C.textMuted, padding: "4px 10px", borderRadius: 4, fontSize: 10, cursor: "pointer", fontFamily: "inherit" }}>✕</button>
              </div>
            </div>
            <pre style={{ flex: 1, overflowY: "auto", padding: 20, margin: 0, fontSize: 11, lineHeight: 1.7, color: C.text, background: C.bg, borderRadius: "0 0 10px 10px" }}>
              {yamlOutput}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}