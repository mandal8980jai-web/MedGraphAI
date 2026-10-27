import React, { useMemo, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Node,
  Edge,
  Panel,
  BackgroundVariant
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { KnowledgeGraphData } from '../../types';
import { MedicineNode } from './MedicineNode';
import { IngredientNode } from './IngredientNode';
import {
  AlertTriangle,
  Info,
  Pill,
  FlaskConical,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';

interface MedicineMapProps {
  graphData?: KnowledgeGraphData | null;
  notice?: string;
  className?: string;
}

const nodeTypes = {
  medicine: MedicineNode,
  ingredient: IngredientNode,
};

export const MedicineMap: React.FC<MedicineMapProps> = ({
  graphData,
  notice = 'Only the medicines and rules in our sample list were checked. A missing warning does not mean there is no interaction.',
  className = '',
}) => {
  // Transform backend graph nodes to React Flow nodes
  const initialNodes: Node[] = useMemo(() => {
    if (!graphData?.nodes || graphData.nodes.length === 0) return [];
    return graphData.nodes.map((n) => ({
      id: n.id,
      type: n.type || 'medicine',
      position: n.position || { x: 100, y: 100 },
      data: {
        label: n.label,
        type: n.type,
        is_known: n.is_known,
        strength: n.strength,
        dose: n.dose,
        match_status: n.match_status,
      },
    }));
  }, [graphData?.nodes]);

  // Transform backend graph edges to React Flow edges with custom styling
  const initialEdges: Edge[] = useMemo(() => {
    if (!graphData?.edges || graphData.edges.length === 0) return [];
    return graphData.edges.map((e, idx) => {
      const isInteracts = e.type === 'interacts';
      const isHighSeverity = isInteracts && e.severity === 'high';
      const isModerateSeverity = isInteracts && e.severity === 'moderate';

      if (isHighSeverity) {
        return {
          id: e.id || `edge-${idx}`,
          source: e.source || e.from,
          target: e.target || e.to,
          type: 'default',
          animated: true,
          label: 'High Risk Interaction',
          labelStyle: {
            fill: '#b91c1c',
            fontWeight: 700,
            fontSize: 11,
          },
          labelBgStyle: {
            fill: '#fef2f2',
            fillOpacity: 0.95,
            stroke: '#ef4444',
            strokeWidth: 1.5,
          },
          labelBgPadding: [8, 4],
          labelBgBorderRadius: 6,
          style: {
            stroke: '#ef4444',
            strokeWidth: 3.5,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#ef4444',
            width: 22,
            height: 22,
          },
        };
      }

      if (isModerateSeverity) {
        return {
          id: e.id || `edge-${idx}`,
          source: e.source || e.from,
          target: e.target || e.to,
          type: 'default',
          animated: false,
          label: 'Moderate Interaction',
          labelStyle: {
            fill: '#b45309',
            fontWeight: 600,
            fontSize: 10,
          },
          labelBgStyle: {
            fill: '#fffbeb',
            fillOpacity: 0.95,
            stroke: '#f59e0b',
            strokeWidth: 1,
          },
          labelBgPadding: [6, 3],
          labelBgBorderRadius: 6,
          style: {
            stroke: '#f59e0b',
            strokeWidth: 2.5,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#f59e0b',
            width: 18,
            height: 18,
          },
        };
      }

      // Default 'contains' edge
      return {
        id: e.id || `edge-${idx}`,
        source: e.source || e.from,
        target: e.target || e.to,
        type: 'smoothstep',
        animated: true,
        style: {
          stroke: '#0d9488',
          strokeWidth: 2,
          strokeDasharray: '5,5',
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#0d9488',
          width: 14,
          height: 14,
        },
      };
    });
  }, [graphData?.edges]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="flex h-96 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 p-8 text-center dark:border-slate-800">
        <Pill className="mb-3 h-10 w-10 text-slate-400" />
        <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          No medicines to display in Medicine Map
        </p>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Confirm medicines in the previous step to generate the interactive network.
        </p>
      </div>
    );
  }

  return (
    <div className={`relative flex flex-col rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 ${className}`}>
      {/* Permanent Notice Banner */}
      <div className="flex items-center space-x-2.5 border-b border-amber-200/80 bg-amber-50/80 px-4 py-2.5 text-xs text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-200">
        <Info className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <span className="font-medium">
          {notice}
        </span>
      </div>

      {/* React Flow Canvas */}
      <div className="relative h-[540px] w-full overflow-hidden rounded-b-2xl">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.25 }}
          minZoom={0.2}
          maxZoom={2}
          nodesDraggable={true}
          nodesConnectable={false}
          elementsSelectable={true}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#94a3b8" />
          <Controls position="bottom-right" className="!border-slate-200 !bg-white !shadow-sm dark:!border-slate-700 dark:!bg-slate-800" />
          <MiniMap
            position="bottom-left"
            className="!hidden sm:!block !rounded-xl !border !border-slate-200 !bg-white/90 !shadow-sm dark:!border-slate-700 dark:!bg-slate-800/90"
            nodeColor={(n) => (n.type === 'ingredient' ? '#10b981' : '#0d9488')}
            maskColor="rgba(100, 116, 139, 0.15)"
          />

          {/* Interactive Legend Panel */}
          <Panel position="top-right" className="m-3">
            <div className="rounded-xl border border-slate-200/80 bg-white/95 p-3.5 shadow-md backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/95 max-w-[230px]">
              <div className="flex items-center space-x-1.5 border-b border-slate-100 pb-2 dark:border-slate-800">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-100">
                  Medicine Map Legend
                </span>
              </div>
              <div className="mt-2.5 space-y-2 text-[11px]">
                <div className="flex items-center space-x-2">
                  <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded-md bg-teal-100 text-teal-700 dark:bg-teal-900/60 dark:text-teal-300">
                    <Pill className="h-2.5 w-2.5" />
                  </div>
                  <span className="text-slate-700 dark:text-slate-300">Medicine Node</span>
                </div>

                <div className="flex items-center space-x-2">
                  <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded-md bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300">
                    <FlaskConical className="h-2.5 w-2.5" />
                  </div>
                  <span className="text-slate-700 dark:text-slate-300">Active Ingredient</span>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="h-0.5 w-4 rounded bg-teal-600 dark:bg-teal-400" />
                  <span className="text-slate-600 dark:text-slate-400">Contains ingredient</span>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="h-1 w-4 rounded bg-rose-600 shadow-sm" />
                  <span className="font-semibold text-rose-600 dark:text-rose-400">
                    High Risk Interaction
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="h-0.5 w-4 rounded bg-amber-500" />
                  <span className="text-amber-700 dark:text-amber-400">Moderate Interaction</span>
                </div>

                <div className="flex items-center space-x-2 pt-1 border-t border-slate-100 dark:border-slate-800 text-[10px] text-slate-500 dark:text-slate-400">
                  <span>💡 Drag nodes to rearrange. Scroll to zoom.</span>
                </div>
              </div>
            </div>
          </Panel>
        </ReactFlow>
      </div>
    </div>
  );
};
