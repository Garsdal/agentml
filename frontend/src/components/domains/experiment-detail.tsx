import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StateBadge } from "@/components/state-badge";
import {
  useExperimentCode,
  useExperimentCodeRun,
} from "@/hooks/use-experiment-code";
import type { Experiment } from "@/types";

interface ExperimentDetailPanelProps {
  experiment: Experiment;
}

export function ExperimentDetailPanel({
  experiment,
}: ExperimentDetailPanelProps) {
  const [activeTab, setActiveTab] = useState("config");
  const [expandedRun, setExpandedRun] = useState<number | null>(null);

  const codeEnabled = activeTab === "code";
  const { data: codeRuns, isLoading: codeLoading } = useExperimentCode(
    experiment.id,
    codeEnabled,
  );
  const { data: codeRunDetail } = useExperimentCodeRun(
    codeEnabled ? experiment.id : undefined,
    expandedRun,
  );

  const hasMetrics =
    experiment.metrics && Object.keys(experiment.metrics).length > 0;
  const hasConfig = Object.keys(experiment.config).length > 0;

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    setExpandedRun(null);
  };

  return (
    <div className="bg-wheat/5 border-t border-soft-fawn/20 px-4 py-4">
      {/* Summary row */}
      <div className="flex items-center gap-3 flex-wrap mb-3">
        <StateBadge state={experiment.state} />
        <span className="font-mono text-xs text-grey">{experiment.id}</span>
        {experiment.hypothesis && (
          <span className="text-xs text-blackberry italic truncate max-w-[400px]">
            &ldquo;{experiment.hypothesis}&rdquo;
          </span>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="mb-3 h-7">
          <TabsTrigger value="config" className="text-xs h-6 px-2.5">
            Config
          </TabsTrigger>
          <TabsTrigger value="metrics" className="text-xs h-6 px-2.5">
            Metrics
          </TabsTrigger>
          <TabsTrigger value="code" className="text-xs h-6 px-2.5">
            Code
          </TabsTrigger>
          {experiment.error && (
            <TabsTrigger
              value="error"
              className="text-xs h-6 px-2.5 text-danger data-[state=active]:text-danger"
            >
              Error
            </TabsTrigger>
          )}
        </TabsList>

        {/* Config tab */}
        <TabsContent value="config">
          {hasConfig ? (
            <div className="space-y-1">
              {Object.entries(experiment.config).map(([k, v]) => (
                <div key={k} className="flex items-start gap-2">
                  <span className="text-xs text-grey shrink-0 pt-0.5">
                    {k}:
                  </span>
                  <span className="text-xs text-blackberry font-mono break-all">
                    {String(v).slice(0, 120)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-grey">No config recorded.</p>
          )}
        </TabsContent>

        {/* Metrics tab */}
        <TabsContent value="metrics">
          {hasMetrics ? (
            <div className="space-y-1 max-w-xs">
              {Object.entries(experiment.metrics!).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between">
                  <span className="text-xs text-grey">{k}</span>
                  <span className="text-xs font-semibold text-blackberry font-mono">
                    {typeof v === "number" ? v.toFixed(4) : String(v)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-grey">No metrics recorded.</p>
          )}
        </TabsContent>

        {/* Code tab */}
        <TabsContent value="code">
          {codeLoading && (
            <p className="text-xs text-grey">Loading code runs…</p>
          )}
          {!codeLoading && (!codeRuns || codeRuns.length === 0) && (
            <p className="text-xs text-grey">
              No code runs recorded for this experiment.
            </p>
          )}
          {codeRuns && codeRuns.length > 0 && (
            <div className="space-y-1.5">
              {codeRuns.map((run) => {
                const isExpanded = expandedRun === run.run_number;
                const isLoadingCode =
                  isExpanded && codeRunDetail?.run_number !== run.run_number;

                return (
                  <div
                    key={run.run_number}
                    className="rounded-lg border border-soft-fawn/20 overflow-hidden"
                  >
                    {/* Run header row */}
                    <button
                      type="button"
                      className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-wheat/10 transition-colors"
                      onClick={() =>
                        setExpandedRun(isExpanded ? null : run.run_number)
                      }
                    >
                      <span className="text-xs font-mono text-grey shrink-0 w-6">
                        #{run.run_number}
                      </span>
                      <span className="text-xs text-blackberry flex-1 truncate">
                        {run.description || "—"}
                      </span>
                      <span
                        className={`text-xs font-mono px-1.5 py-0.5 rounded shrink-0 ${
                          run.exit_code === 0
                            ? "bg-muted-teal/15 text-muted-teal"
                            : "bg-danger/10 text-danger"
                        }`}
                      >
                        exit {run.exit_code}
                      </span>
                      <span className="text-xs text-grey shrink-0">
                        {(run.duration_ms / 1000).toFixed(1)}s
                      </span>
                      <span className="text-grey shrink-0 text-xs">
                        {isExpanded ? "▾" : "▸"}
                      </span>
                    </button>

                    {/* Code viewer */}
                    {isExpanded && (
                      <div className="border-t border-soft-fawn/20">
                        {isLoadingCode ? (
                          <p className="text-xs text-grey p-3">Loading…</p>
                        ) : (
                          <pre className="text-[10px] font-mono bg-blackberry/5 text-blackberry p-3 max-h-[320px] overflow-auto whitespace-pre-wrap leading-relaxed">
                            {codeRunDetail?.code ?? ""}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Error tab */}
        {experiment.error && (
          <TabsContent value="error">
            <pre className="text-xs font-mono bg-danger/10 text-danger rounded-lg p-3 overflow-auto max-h-40 whitespace-pre-wrap">
              {experiment.error}
            </pre>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
