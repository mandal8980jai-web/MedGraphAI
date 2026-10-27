import React from 'react';
import { ExternalLink, ShieldCheck, AlertTriangle, TrendingDown, Layers, CheckCircle } from 'lucide-react';
import { AlternativesData } from '../../types';

interface AlternativesCardProps {
  data: AlternativesData;
}

export const AlternativesCard: React.FC<AlternativesCardProps> = ({ data }) => {
  if (!data || data.status !== 'ok') {
    return null;
  }

  const hasBrands = data.category_b_brands && data.category_b_brands.length > 0;
  const hasGenerics = data.category_c_generics && data.category_c_generics.length > 0;
  const hasNonInterchangeable = data.category_d_non_interchangeable && data.category_d_non_interchangeable.length > 0;

  if (!hasBrands && !hasGenerics && !hasNonInterchangeable) {
    return null;
  }

  return (
    <div className="mt-3 rounded-2xl border border-indigo-100 bg-indigo-50/40 p-3.5 sm:p-4 text-xs dark:border-indigo-900/40 dark:bg-indigo-950/20 space-y-3.5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-indigo-100/80 pb-2 dark:border-indigo-900/40">
        <div className="flex items-center space-x-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <h4 className="font-bold text-slate-900 dark:text-white">
              Affordable Brand & Generic Alternatives
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Verified bioequivalent formulations sharing the exact same active salt & strength.
            </p>
          </div>
        </div>

        <span className="inline-flex items-center space-x-1 rounded-md bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold text-indigo-700 dark:bg-indigo-950/80 dark:text-indigo-300">
          <ShieldCheck className="h-3 w-3" />
          <span>Equivalence Checked</span>
        </span>
      </div>

      {/* Category C: Jan Aushadhi & Generic Substitutes */}
      {hasGenerics && (
        <div className="space-y-2">
          <div className="flex items-center space-x-1.5 font-semibold text-[11px] text-emerald-800 dark:text-emerald-300">
            <CheckCircle className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Category C: Jan Aushadhi & Low-Cost Generics</span>
          </div>

          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {data.category_c_generics.map((gen, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-emerald-200 bg-white p-3 dark:border-emerald-900/40 dark:bg-slate-900 shadow-sm flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-1">
                    <h5 className="font-semibold text-slate-900 dark:text-white">
                      {gen.product_name}
                    </h5>
                    {gen.savings_percentage && gen.savings_percentage > 0 && (
                      <span className="inline-flex items-center space-x-0.5 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 shrink-0">
                        <TrendingDown className="h-3 w-3" />
                        <span>~{gen.savings_percentage}% less</span>
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                    {gen.manufacturer} • {gen.pack_size}
                  </p>
                  <p className="text-[11px] text-slate-700 dark:text-slate-300 mt-1.5 font-medium">
                    Verified Reference Price: ₹{gen.verified_mrp_inr}
                  </p>
                </div>

                <div className="mt-2.5 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px]">
                  <span className="text-slate-500">{gen.safety_note}</span>
                  <a
                    href={`https://janaushadhi.gov.in/ProductList.aspx`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1 text-emerald-600 hover:text-emerald-500 font-semibold dark:text-emerald-400 shrink-0 ml-2"
                  >
                    <span>Jan Aushadhi Portal</span>
                    <ExternalLink className="h-2.5 w-2.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Category B: Equivalent Other Brands */}
      {hasBrands && (
        <div className="space-y-2">
          <div className="flex items-center space-x-1.5 font-semibold text-[11px] text-indigo-800 dark:text-indigo-300">
            <Layers className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
            <span>Category B: Equivalent Brands (Same Active Salt & Strength)</span>
          </div>

          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {data.category_b_brands.map((brand, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 shadow-sm flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-1">
                    <h5 className="font-semibold text-slate-900 dark:text-white">
                      {brand.brand_name}
                    </h5>
                    {brand.savings_percentage && brand.savings_percentage > 0 && (
                      <span className="inline-flex items-center space-x-0.5 rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-bold text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 shrink-0">
                        <TrendingDown className="h-3 w-3" />
                        <span>~{brand.savings_percentage}% less</span>
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                    {brand.manufacturer} • {brand.pack_size}
                  </p>
                  <p className="text-[11px] text-slate-700 dark:text-slate-300 mt-1.5 font-medium">
                    Verified Reference Price: ₹{brand.verified_mrp_inr}
                  </p>
                </div>

                <div className="mt-2.5 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px]">
                  <span className="text-slate-500 truncate max-w-[180px]">{brand.equivalence_rationale}</span>
                  <a
                    href={`https://www.1mg.com/search/all?name=${encodeURIComponent(brand.brand_name)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1 text-indigo-600 hover:text-indigo-500 font-semibold dark:text-indigo-400 shrink-0 ml-2"
                  >
                    <span>View Brand</span>
                    <ExternalLink className="h-2.5 w-2.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Category D: Distinct Medicine Classes (Strictly NOT Interchangeable) */}
      {hasNonInterchangeable && (
        <div className="rounded-xl border border-rose-200 bg-rose-50/80 p-3 text-[11px] text-rose-900 dark:border-rose-900/40 dark:bg-rose-950/30 dark:text-rose-200 space-y-1.5">
          <div className="flex items-center space-x-1.5 font-bold">
            <AlertTriangle className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" />
            <span>Category D: Different Medicine Classes — NEVER Interchangeable</span>
          </div>
          {data.category_d_non_interchangeable.map((diff, idx) => (
            <div key={idx} className="pl-5 text-[10px] leading-relaxed">
              <strong>{diff.drug_name}:</strong> {diff.warning}
            </div>
          ))}
        </div>
      )}

      {/* Substitution Medical Disclaimer */}
      <p className="text-[10px] text-slate-500 dark:text-slate-400 italic">
        {data.substitution_notice}
      </p>
    </div>
  );
};
