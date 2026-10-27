import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { FlaskConical } from 'lucide-react';

export interface IngredientNodeData {
  label: string;
}

export const IngredientNode: React.FC<NodeProps> = memo(({ data }) => {
  const nodeData = data as unknown as IngredientNodeData;

  return (
    <div className="rounded-2xl border border-emerald-400 bg-emerald-50/95 p-3 min-w-[160px] max-w-[210px] shadow-md shadow-emerald-500/10 backdrop-blur-sm dark:border-emerald-600/70 dark:bg-emerald-950/80">
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-emerald-500 dark:!border-slate-900"
      />

      <div className="flex items-center space-x-2.5">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300">
          <FlaskConical className="h-3.5 w-3.5" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="block text-[10px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
            Active Ingredient
          </span>
          <p className="truncate text-xs font-bold capitalize text-slate-900 dark:text-white" title={nodeData.label}>
            {nodeData.label}
          </p>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-emerald-500 dark:!border-slate-900"
      />
    </div>
  );
});

IngredientNode.displayName = 'IngredientNode';
