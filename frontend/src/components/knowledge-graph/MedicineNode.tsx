import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Pill, AlertCircle, CheckCircle2 } from 'lucide-react';

export interface MedicineNodeData {
  label: string;
  is_known?: boolean;
  strength?: string | null;
  dose?: string | null;
  match_status?: string;
}

export const MedicineNode: React.FC<NodeProps> = memo(({ data }) => {
  const nodeData = data as unknown as MedicineNodeData;
  const isUnknown = nodeData.is_known === false;

  return (
    <div
      className={`rounded-2xl border p-3.5 min-w-[190px] max-w-[240px] shadow-md backdrop-blur-sm transition-all ${
        isUnknown
          ? 'border-amber-400 bg-amber-50/95 dark:border-amber-600 dark:bg-amber-950/80 shadow-amber-500/10'
          : 'border-teal-500 bg-white/95 dark:border-teal-500/70 dark:bg-slate-900/95 shadow-teal-500/10'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-teal-500 dark:!border-slate-900"
      />

      <div className="flex items-start space-x-2.5">
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${
            isUnknown
              ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-300'
              : 'bg-teal-100 text-teal-700 dark:bg-teal-900/60 dark:text-teal-300'
          }`}
        >
          <Pill className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-bold text-slate-900 dark:text-white" title={nodeData.label}>
            {nodeData.label}
          </p>
          {(nodeData.strength || nodeData.dose) && (
            <p className="truncate text-[11px] text-slate-500 dark:text-slate-400">
              {[nodeData.strength, nodeData.dose].filter(Boolean).join(' • ')}
            </p>
          )}
        </div>
      </div>

      <div className="mt-2.5 flex items-center justify-between border-t border-slate-100 pt-2 dark:border-slate-800">
        <div className="flex items-center space-x-1">
          {isUnknown ? (
            <>
              <AlertCircle className="h-3 w-3 text-amber-600 dark:text-amber-400" />
              <span className="text-[10px] font-semibold text-amber-700 dark:text-amber-300">
                Not in sample list
              </span>
            </>
          ) : (
            <>
              <CheckCircle2 className="h-3 w-3 text-teal-600 dark:text-teal-400" />
              <span className="text-[10px] font-semibold text-teal-700 dark:text-teal-300">
                Sample Catalog
              </span>
            </>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-teal-500 dark:!border-slate-900"
      />
    </div>
  );
});

MedicineNode.displayName = 'MedicineNode';
