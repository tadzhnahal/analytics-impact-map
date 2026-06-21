import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Background,
  Controls,
  Edge,
  MarkerType,
  MiniMap,
  Node,
  ReactFlow,
  useEdgesState,
  useNodesState
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { ComponentProps, Streamlit } from "streamlit-component-lib";

type RawNode = {
  id: string;
  label: string;
  node_type?: string;
  description?: string;
  x?: number;
  y?: number;
  status?: string;
  selected?: boolean;
};

type RawEdge = {
  id: string;
  source: string;
  target: string;
  label?: string;
  dependency_type?: string;
  selected?: boolean;
};

type CanvasEvent = {
  event_type: string;
  target_type: string;
  node_ids: string[];
  edge_ids: string[];
  positions: Record<string, { x: number; y: number }>;
  payload?: Record<string, unknown>;
};

function getNodeClass(status?: string) {
  if (status === "root") {
    return "graph-node graph-node-root";
  }

  if (status === "affected") {
    return "graph-node graph-node-affected";
  }

  return "graph-node graph-node-normal";
}

function buildNode(item: RawNode, index: number): Node {
  const x = item.x ?? 120 + (index % 4) * 220;
  const y = item.y ?? 80 + Math.floor(index / 4) * 140;

  return {
    id: String(item.id),
    position: { x, y },
    selected: item.selected ?? false,
    data: {
      label: item.label,
      node_type: item.node_type,
      description: item.description
    },
    className: getNodeClass(item.status),
    type: "default",
    draggable: true,
    selectable: true
  };
}

function buildNodes(rawNodes: RawNode[]): Node[] {
  return rawNodes.map((item, index) => buildNode(item, index));
}

function mergeNodes(rawNodes: RawNode[], currentNodes: Node[], resetLayout: boolean): Node[] {
  const currentNodeMap = new Map<string, Node>();

  for (const node of currentNodes) {
    currentNodeMap.set(node.id, node);
  }

  return rawNodes.map((item, index) => {
    const nextNode = buildNode(item, index);
    const currentNode = currentNodeMap.get(nextNode.id);

    if (currentNode && !resetLayout) {
      nextNode.position = currentNode.position;
    }

    return nextNode;
  });
}

function buildEdges(rawEdges: RawEdge[]): Edge[] {
  return rawEdges.map((item) => {
    const label = item.label ?? item.dependency_type ?? "";

    return {
      id: String(item.id),
      source: String(item.source),
      target: String(item.target),
      label,
      selected: item.selected ?? false,
      animated: false,
      markerEnd: {
        type: MarkerType.ArrowClosed
      },
      className: "graph-edge",
      selectable: true
    };
  });
}

function buildPositions(nodes: Node[]) {
  const positions: Record<string, { x: number; y: number }> = {};

  for (const node of nodes) {
    positions[node.id] = {
      x: node.position.x,
      y: node.position.y
    };
  }

  return positions;
}

function getSafeNodeId(rawNodes: RawNode[], currentValue: string) {
  if (rawNodes.length === 0) {
    return "";
  }

  for (const node of rawNodes) {
    if (node.id === currentValue) {
      return currentValue;
    }
  }

  return rawNodes[0].id;
}

function GraphCanvas(props: ComponentProps) {
  const rawNodes = (props.args["nodes"] ?? []) as RawNode[];
  const rawEdges = (props.args["edges"] ?? []) as RawEdge[];
  const height = (props.args["height"] ?? 680) as number;
  const analysisMode = (props.args["analysis_mode"] ?? false) as boolean;
  const layoutVersion = (props.args["layout_version"] ?? 0) as number;

  const initialNodes = useMemo(() => buildNodes(rawNodes), [rawNodes]);
  const initialEdges = useMemo(() => buildEdges(rawEdges), [rawEdges]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const [menuOpen, setMenuOpen] = useState(false);
  const [menuTab, setMenuTab] = useState<"component" | "dependency">("component");

  const [componentName, setComponentName] = useState("");
  const [componentType, setComponentType] = useState("source");
  const [componentDescription, setComponentDescription] = useState("");

  const [sourceNodeId, setSourceNodeId] = useState("");
  const [targetNodeId, setTargetNodeId] = useState("");
  const [dependencyType, setDependencyType] = useState("hard");

  const [spacePressed, setSpacePressed] = useState(false);

  const latestNodesRef = useRef<Node[]>(initialNodes);
  const latestEdgesRef = useRef<Edge[]>(initialEdges);
  const layoutVersionRef = useRef(layoutVersion);

  const selectionChangedRef = useRef(false);
  const selectedNodeIdsRef = useRef<string[]>([]);
  const selectedEdgeIdsRef = useRef<string[]>([]);

  const nodeDragHappenedRef = useRef(false);
  const skipNextSelectionSendRef = useRef(false);
  const ignoreNextPaneClickRef = useRef(false);

  useEffect(() => {
    latestNodesRef.current = nodes;
  }, [nodes]);

  useEffect(() => {
    latestEdgesRef.current = edges;
  }, [edges]);

  useEffect(() => {
    const resetLayout = layoutVersionRef.current !== layoutVersion;
    layoutVersionRef.current = layoutVersion;

    setNodes((currentNodes) => {
      const mergedNodes = mergeNodes(rawNodes, currentNodes, resetLayout);
      latestNodesRef.current = mergedNodes;
      return mergedNodes;
    });

    setEdges(buildEdges(rawEdges));

    setSourceNodeId((currentValue) => getSafeNodeId(rawNodes, currentValue));
    setTargetNodeId((currentValue) => getSafeNodeId(rawNodes, currentValue));
  }, [rawNodes, rawEdges, layoutVersion, setNodes, setEdges]);

  useEffect(() => {
    Streamlit.setFrameHeight(height + 20);
  }, [height]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code === "Space") {
        event.preventDefault();
        setSpacePressed(true);
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.code === "Space") {
        event.preventDefault();
        setSpacePressed(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  useEffect(() => {
    const sendSelectionOnMouseUp = () => {
      if (nodeDragHappenedRef.current) {
        nodeDragHappenedRef.current = false;
        selectionChangedRef.current = false;
        return;
      }

      if (skipNextSelectionSendRef.current) {
        skipNextSelectionSendRef.current = false;
        selectionChangedRef.current = false;
        return;
      }

      if (!selectionChangedRef.current) {
        return;
      }

      selectionChangedRef.current = false;
      ignoreNextPaneClickRef.current = true;

      sendEvent({
        event_type: "selection_change",
        target_type: "selection",
        node_ids: selectedNodeIdsRef.current,
        edge_ids: selectedEdgeIdsRef.current,
        positions: buildPositions(latestNodesRef.current)
      });

      window.setTimeout(() => {
        ignoreNextPaneClickRef.current = false;
      }, 250);
    };

    window.addEventListener("mouseup", sendSelectionOnMouseUp);

    return () => {
      window.removeEventListener("mouseup", sendSelectionOnMouseUp);
    };
  }, []);

  const sendEvent = useCallback((event: CanvasEvent) => {
    Streamlit.setComponentValue({
      ...event,
      timestamp: Date.now()
    });
  }, []);

  const sendSimpleEvent = useCallback(
    (
      eventType: string,
      targetType: string,
      nodeIds: string[],
      edgeIds: string[],
      payload?: Record<string, unknown>
    ) => {
      sendEvent({
        event_type: eventType,
        target_type: targetType,
        node_ids: nodeIds,
        edge_ids: edgeIds,
        positions: buildPositions(latestNodesRef.current),
        payload
      });
    },
    [sendEvent]
  );

  const handleSelectionChange = useCallback((selectedNodes: Node[], selectedEdges: Edge[]) => {
    selectedNodeIdsRef.current = selectedNodes.map((node) => node.id);
    selectedEdgeIdsRef.current = selectedEdges.map((edge) => edge.id);
    selectionChangedRef.current = true;
  }, []);

  const createComponent = () => {
    const cleanName = componentName.trim();

    if (!cleanName) {
      return;
    }

    sendSimpleEvent("create_component", "toolbar", [], [], {
      name: cleanName,
      component_type: componentType,
      description: componentDescription.trim()
    });

    setComponentName("");
    setComponentDescription("");
    setMenuOpen(false);
  };

  const createDependency = () => {
    if (!sourceNodeId || !targetNodeId || sourceNodeId === targetNodeId) {
      return;
    }

    sendSimpleEvent("create_dependency", "toolbar", [], [], {
      source_component_id: sourceNodeId,
      target_component_id: targetNodeId,
      dependency_type: dependencyType
    });

    setMenuOpen(false);
  };

  return (
    <div className={spacePressed ? "graph-canvas-shell graph-space-mode" : "graph-canvas-shell"} style={{ height }}>
      <div
        className="graph-floating-tools"
        onClick={(event) => event.stopPropagation()}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button
          className="graph-tool-button"
          title="Создать компонент или связь"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          +
        </button>

        <button
          className={analysisMode ? "graph-tool-button graph-tool-active" : "graph-tool-button"}
          title="Анализ"
          onClick={() => sendSimpleEvent("toggle_analysis_mode", "toolbar", [], [])}
        >
          ◎
        </button>

        <button
          className="graph-tool-button"
          title="Сбросить раскладку"
          onClick={() => sendSimpleEvent("reset_layout", "toolbar", [], [])}
        >
          ↻
        </button>

        {menuOpen && (
          <div className="graph-create-menu">
            <div className="graph-menu-tabs">
              <button
                className={menuTab === "component" ? "graph-menu-tab-active" : ""}
                onClick={() => setMenuTab("component")}
              >
                Компонент
              </button>
              <button
                className={menuTab === "dependency" ? "graph-menu-tab-active" : ""}
                onClick={() => setMenuTab("dependency")}
              >
                Связь
              </button>
            </div>

            {menuTab === "component" && (
              <div className="graph-menu-form">
                <label>
                  Название
                  <input
                    value={componentName}
                    onChange={(event) => setComponentName(event.target.value)}
                    placeholder="events_mart"
                  />
                </label>

                <label>
                  Тип
                  <select
                    value={componentType}
                    onChange={(event) => setComponentType(event.target.value)}
                  >
                    <option value="source">source</option>
                    <option value="mart">mart</option>
                    <option value="dashboard">dashboard</option>
                    <option value="service">service</option>
                    <option value="report">report</option>
                    <option value="other">other</option>
                  </select>
                </label>

                <label>
                  Описание
                  <textarea
                    value={componentDescription}
                    onChange={(event) => setComponentDescription(event.target.value)}
                    placeholder="Короткое описание"
                  />
                </label>

                <button
                  className="graph-menu-submit"
                  type="button"
                  onClick={createComponent}
                >
                  Создать
                </button>
              </div>
            )}

            {menuTab === "dependency" && (
              <div className="graph-menu-form">
                <label>
                  Откуда
                  <select
                    value={sourceNodeId}
                    onChange={(event) => setSourceNodeId(event.target.value)}
                  >
                    {rawNodes.map((node) => (
                      <option key={node.id} value={node.id}>
                        {node.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Куда
                  <select
                    value={targetNodeId}
                    onChange={(event) => setTargetNodeId(event.target.value)}
                  >
                    {rawNodes.map((node) => (
                      <option key={node.id} value={node.id}>
                        {node.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Тип
                  <select
                    value={dependencyType}
                    onChange={(event) => setDependencyType(event.target.value)}
                  >
                    <option value="hard">hard</option>
                    <option value="soft">soft</option>
                  </select>
                </label>

                <button
                  className="graph-menu-submit"
                  type="button"
                  onClick={createDependency}
                  disabled={rawNodes.length < 2 || sourceNodeId === targetNodeId}
                >
                  Создать
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {analysisMode && (
        <div className="graph-mode-badge">
          Анализ: кликните по узлу
        </div>
      )}

      {spacePressed && (
        <div className="graph-space-badge">
          Перемещение карты
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        panOnDrag={spacePressed}
        zoomOnScroll
        zoomOnPinch
        zoomOnDoubleClick={false}
        nodesDraggable
        nodesConnectable={false}
        edgesFocusable
        nodesFocusable
        elementsSelectable
        selectionOnDrag={!spacePressed}
        selectionKeyCode={null}
        multiSelectionKeyCode={["Meta", "Control", "Shift"]}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onPaneClick={() => {
          if (ignoreNextPaneClickRef.current) {
            return;
          }

          sendSimpleEvent("pane_click", "pane", [], []);
        }}
        onNodeClick={(event, node) => {
          if (analysisMode) {
            sendSimpleEvent("run_analysis", "node", [node.id], []);
            return;
          }

          const isMultiClick = event.shiftKey || event.ctrlKey || event.metaKey;

          if (isMultiClick) {
            return;
          }

          skipNextSelectionSendRef.current = true;
          sendSimpleEvent("node_click", "node", [node.id], []);
        }}
        onNodeDoubleClick={(event) => {
          event.preventDefault();
        }}
        onNodeContextMenu={(event, node) => {
          event.preventDefault();
          skipNextSelectionSendRef.current = true;
          sendSimpleEvent("node_context_menu", "node", [node.id], []);
        }}
        onEdgeClick={(_, edge) => {
          skipNextSelectionSendRef.current = true;
          sendSimpleEvent("edge_click", "edge", [], [edge.id]);
        }}
        onEdgeContextMenu={(event, edge) => {
          event.preventDefault();
          skipNextSelectionSendRef.current = true;
          sendSimpleEvent("edge_context_menu", "edge", [], [edge.id]);
        }}
        onNodeDragStart={() => {
          nodeDragHappenedRef.current = true;
        }}
        onNodeDragStop={(_, node) => {
          window.requestAnimationFrame(() => {
            sendEvent({
              event_type: "node_drag_stop",
              target_type: "node",
              node_ids: [node.id],
              edge_ids: [],
              positions: buildPositions(latestNodesRef.current)
            });
          });
        }}
        onSelectionChange={({ nodes: selectedNodes, edges: selectedEdges }) => {
          handleSelectionChange(selectedNodes, selectedEdges);
        }}
        proOptions={{ hideAttribution: true }}
      >
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}

export default GraphCanvas;
