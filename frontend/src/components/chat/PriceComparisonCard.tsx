import React from 'react';
import { ExternalLink, ShieldCheck, AlertCircle, ShoppingBag, Info, Clock } from 'lucide-react';
import { PriceComparisonData } from '../../types';

interface PriceComparisonCardProps {
  data: PriceComparisonData;
}

export const PriceComparisonCard: React.FC<PriceComparisonCardProps> = ({ data }) => {
  if (!data || !data.providers_compared || data.providers_compared.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 rounded-2xl border border-teal-100 bg-teal-50/40 p-3.5 sm:p-4 text-xs dark:border-teal-900/40 dark:bg-teal-950/20 space-y-3.5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-teal-100/80 pb-2.5 dark:border-teal-900/40">
        <div className="flex items-center space-x-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-600 text-white shadow-sm">
            <ShoppingBag className="h-4 w-4" />
          </div>
          <div>
            <h4 className="font-bold text-slate-900 dark:text-white">
              Pharmacy Price Comparison & Links
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {data.medicine_name} {data.strength ? `• ${data.strength}` : ''} {data.dosage_form ? `• ${data.dosage_form}` : ''}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 text-[10px] text-slate-500 dark:text-slate-400">
          <Clock className="h-3 w-3" />
          <span>{data.retrieval_timestamp || 'Just now'}</span>
        </div>
      </div>

      {/* Benchmark Reference Notice if available */}
      {data.reference_benchmark_mrp && (
        <div className="flex items-center space-x-2 rounded-xl border border-slate-200/80 bg-white/80 p-2.5 dark:border-slate-800 dark:bg-slate-900/80 text-[11px] text-slate-700 dark:text-slate-300">
          <Info className="h-3.5 w-3.5 text-teal-600 shrink-0 dark:text-teal-400" />
          <span>
            <strong>Reference Benchmark MRP:</strong> ₹{data.reference_benchmark_mrp} ({data.pack_size || 'standard pack'}).
            Retail prices may vary by pharmacy and ongoing offers.
          </span>
        </div>
      )}

      {/* Comparison Table / Responsive Cards */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 shadow-sm">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/75 dark:border-slate-800 dark:bg-slate-800/50 text-[11px] font-semibold text-slate-600 dark:text-slate-300">
              <th className="py-2.5 px-3">Pharmacy</th>
              <th className="py-2.5 px-3">Pack Size</th>
              <th className="py-2.5 px-3">Price Verification</th>
              <th className="py-2.5 px-3">Availability</th>
              <th className="py-2.5 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-[11px]">
            {data.providers_compared.map((item, idx) => (
              <tr key={idx} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                <td className="py-2.5 px-3 font-semibold text-slate-900 dark:text-white">
                  <div className="flex items-center space-x-1.5">
                    <span className="h-2 w-2 rounded-full bg-teal-500"></span>
                    <span>{item.pharmacy_name}</span>
                  </div>
                </td>
                <td className="py-2.5 px-3 text-slate-600 dark:text-slate-300">
                  {item.pack_size || 'Standard strip'}
                </td>
                <td className="py-2.5 px-3">
                  {item.price_status === 'unverified_link_only' ? (
                    <span className="inline-flex items-center space-x-1 text-slate-500 dark:text-slate-400">
                      <span>Check live price</span>
                    </span>
                  ) : item.verified_price ? (
                    <span className="font-bold text-emerald-600 dark:text-emerald-400">
                      ₹{item.verified_price}
                    </span>
                  ) : (
                    <span className="text-slate-400">Not verified</span>
                  )}
                </td>
                <td className="py-2.5 px-3 text-slate-500 dark:text-slate-400 text-[10px]">
                  {item.availability}
                </td>
                <td className="py-2.5 px-3 text-right">
                  <a
                    href={item.direct_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1 rounded-lg bg-teal-600 px-2.5 py-1 text-[11px] font-medium text-white shadow-sm hover:bg-teal-500 dark:bg-teal-500 dark:hover:bg-teal-400 transition-colors"
                  >
                    <span>View at {item.pharmacy_name.split(' ')[0]}</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Honest Link-Only Notice */}
      <div className="flex items-start space-x-2 text-[11px] text-slate-600 dark:text-slate-400 leading-normal">
        <Info className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
        <p>
          {data.price_honesty_note ||
            'Price not verified — check the pharmacy website. Direct search links are provided above to check live pricing and pin-code stock.'}
        </p>
      </div>

      {/* Safety & Prescription Disclaimer */}
      <div className="rounded-xl border border-amber-200/80 bg-amber-50/70 p-2.5 dark:border-amber-900/40 dark:bg-amber-950/20 text-[10px] text-amber-800 dark:text-amber-300 flex items-start space-x-2">
        <AlertCircle className="h-3.5 w-3.5 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
        <div>
          <p className="font-semibold">Prescription & Clinical Suitability Notice:</p>
          <p>{data.safety_disclaimer}</p>
        </div>
      </div>
    </div>
  );
};
