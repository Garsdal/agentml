import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { addDomainTool, removeDomainTool } from "@/hooks/use-domain";
import {
  scanWorkspace,
  type WorkspaceScanSuggestion,
} from "@/hooks/use-workspace";
import { apiFetch } from "@/lib/api";
import type { DomainTool } from "@/types";

interface GeneratedTool {
  name: string;
  description: string;
  type: string;
  example_usage: string;
  parameters: Record<string, unknown>;
}

interface ToolsSectionProps {
  domainId: string;
  tools: DomainTool[];
  hasWorkspace: boolean;
  onMutate: () => void;
}

export function ToolsSection({
  domainId,
  tools,
  hasWorkspace,
  onMutate,
}: ToolsSectionProps) {
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [exampleUsage, setExampleUsage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [expandedToolId, setExpandedToolId] = useState<string | null>(null);
  const [isExecutable, setIsExecutable] = useState(false);
  const [code, setCode] = useState("");
  const [returnDescription, setReturnDescription] = useState("");

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setIsSubmitting(true);
    try {
      await addDomainTool(domainId, {
        name: name.trim(),
        description,
        example_usage: exampleUsage,
        type: "custom",
        created_by: "human",
        executable: isExecutable,
        code,
        return_description: returnDescription,
      });
      setName("");
      setDescription("");
      setExampleUsage("");
      setIsExecutable(false);
      setCode("");
      setReturnDescription("");
      setShowForm(false);
      onMutate();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRemove = async (toolId: string) => {
    await removeDomainTool(domainId, toolId);
    onMutate();
  };

  return (
    <div className="space-y-3">
      {tools.length === 0 && !showForm && (
        <p className="text-sm text-grey">
          No custom tools. Add tools to extend the agent's capabilities.
        </p>
      )}

      {tools.map((tool) => (
        <div
          key={tool.id}
          className="bg-white rounded-xl border border-soft-fawn/20 hover:border-soft-fawn/40 p-4 transition-colors flex items-start justify-between"
        >
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-blackberry text-sm">
                {tool.name}
              </span>
              <span className="bg-wheat/20 text-blackberry rounded-full text-xs px-2 py-0.5">
                {tool.type}
              </span>
              {tool.created_by === "ai" ? (
                <span className="bg-soft-fawn/20 text-soft-fawn rounded-full text-xs px-2 py-0.5">
                  ai
                </span>
              ) : (
                <span className="bg-grey/15 text-grey rounded-full text-xs px-2 py-0.5">
                  human
                </span>
              )}
              {tool.executable && (
                <span className="bg-muted-teal/20 text-muted-teal rounded-full text-xs px-2 py-0.5 font-medium">
                  executable
                </span>
              )}
            </div>
            {tool.description && (
              <p className="text-grey text-xs">{tool.description}</p>
            )}
            {tool.executable && tool.code && (
              <>
                <button
                  type="button"
                  className="text-xs text-grey hover:text-blackberry transition-colors flex items-center gap-1 mt-1"
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpandedToolId(
                      expandedToolId === tool.id ? null : tool.id,
                    );
                  }}
                >
                  <span>{expandedToolId === tool.id ? "▾" : "▸"}</span>
                  {expandedToolId === tool.id ? "Hide code" : "View code"}
                </button>
                {expandedToolId === tool.id && (
                  <pre className="mt-2 text-[10px] font-mono bg-blackberry/5 rounded-lg text-blackberry p-3 max-h-[200px] overflow-auto whitespace-pre-wrap">
                    {tool.code}
                  </pre>
                )}
              </>
            )}
            {tool.return_description && (
              <p className="text-[10px] text-grey mt-1">
                Returns: {tool.return_description}
              </p>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-grey hover:text-danger"
            onClick={() => handleRemove(tool.id)}
          >
            Remove
          </Button>
        </div>
      ))}

      {showForm ? (
        <form
          onSubmit={handleAdd}
          className="space-y-3 rounded-xl border border-soft-fawn/20 p-4"
        >
          <Input
            placeholder="Tool name (e.g. load_dataset)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Input
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <Textarea
            placeholder="Example usage (optional Python snippet)"
            value={exampleUsage}
            onChange={(e) => setExampleUsage(e.target.value)}
            className="min-h-[80px] resize-none font-mono text-xs"
          />
          {/* Executable toggle */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="executable-toggle"
              checked={isExecutable}
              onChange={(e) => setIsExecutable(e.target.checked)}
              className="accent-blackberry"
            />
            <label
              htmlFor="executable-toggle"
              className="text-sm text-blackberry cursor-pointer"
            >
              Executable (callable MCP tool)
            </label>
          </div>
          {isExecutable && (
            <>
              <Textarea
                placeholder="Python function body — code that runs in the workspace"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="min-h-[120px] resize-y font-mono text-xs"
              />
              <Input
                placeholder="Return description (e.g. Dict with shape, columns, head)"
                value={returnDescription}
                onChange={(e) => setReturnDescription(e.target.value)}
              />
            </>
          )}
          <div className="flex gap-2">
            <Button
              type="submit"
              size="sm"
              disabled={!name.trim() || isSubmitting}
            >
              {isSubmitting ? "Adding…" : "Add Tool"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowForm(false)}
            >
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <div className="flex gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={() => setShowForm(true)}>
            + Add Tool
          </Button>
          <GenerateToolsButton domainId={domainId} onMutate={onMutate} />
          {hasWorkspace && (
            <ScanWorkspaceButton domainId={domainId} onMutate={onMutate} />
          )}
        </div>
      )}
    </div>
  );
}

function GenerateToolsButton({
  domainId,
  onMutate,
}: {
  domainId: string;
  onMutate: () => void;
}) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generated, setGenerated] = useState<GeneratedTool[]>([]);
  const [hint, setHint] = useState("");
  const [showHint, setShowHint] = useState(false);
  const [isAdding, setIsAdding] = useState<string | null>(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const result = await apiFetch<{
        generated: GeneratedTool[];
      }>(`/domains/${domainId}/tools/generate`, {
        method: "POST",
        body: JSON.stringify({ hint }),
      });
      setGenerated(result.generated);
      setShowHint(false);
    } catch {
      // Silently handle — backend may not support completions
      setGenerated([]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApprove = async (tool: GeneratedTool) => {
    setIsAdding(tool.name);
    try {
      await addDomainTool(domainId, {
        name: tool.name,
        description: tool.description,
        type: tool.type,
        example_usage: tool.example_usage,
        parameters: tool.parameters,
        created_by: "ai",
      });
      setGenerated((prev) => prev.filter((t) => t.name !== tool.name));
      onMutate();
    } finally {
      setIsAdding(null);
    }
  };

  if (generated.length > 0) {
    return (
      <div className="space-y-3 w-full">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-grey">
            AI-Generated Tools (review & approve)
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs"
            onClick={() => setGenerated([])}
          >
            Dismiss
          </Button>
        </div>
        {generated.map((tool) => (
          <div
            key={tool.name}
            className="rounded-xl border border-dashed border-soft-fawn/40 bg-wheat/5 p-4 space-y-2"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-blackberry text-sm">
                  {tool.name}
                </span>
                <span className="bg-wheat/20 text-blackberry rounded-full text-xs px-2 py-0.5">
                  {tool.type}
                </span>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleApprove(tool)}
                disabled={isAdding === tool.name}
              >
                {isAdding === tool.name ? "Adding…" : "Approve"}
              </Button>
            </div>
            <p className="text-grey text-xs">{tool.description}</p>
            {tool.example_usage && (
              <pre className="text-[10px] font-mono bg-blackberry/5 rounded-lg text-blackberry p-2 max-h-[120px] overflow-auto">
                {tool.example_usage}
              </pre>
            )}
          </div>
        ))}
      </div>
    );
  }

  if (showHint) {
    return (
      <div className="flex gap-2 items-center">
        <Input
          placeholder="Hint (e.g. data loaders for CSV files)"
          value={hint}
          onChange={(e) => setHint(e.target.value)}
          className="text-xs h-8"
        />
        <Button size="sm" onClick={handleGenerate} disabled={isGenerating}>
          {isGenerating ? "Generating…" : "Generate"}
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setShowHint(false)}>
          Cancel
        </Button>
      </div>
    );
  }

  return (
    <Button variant="outline" size="sm" onClick={() => setShowHint(true)}>
      ✨ AI Generate
    </Button>
  );
}

function ScanWorkspaceButton({
  domainId,
  onMutate,
}: {
  domainId: string;
  onMutate: () => void;
}) {
  const [isScanning, setIsScanning] = useState(false);
  const [suggestions, setSuggestions] = useState<WorkspaceScanSuggestion[]>([]);
  const [isAdding, setIsAdding] = useState<string | null>(null);

  const handleScan = async () => {
    setIsScanning(true);
    try {
      const result = await scanWorkspace(domainId);
      setSuggestions(result.suggestions);
    } catch {
      setSuggestions([]);
    } finally {
      setIsScanning(false);
    }
  };

  const handleApprove = async (s: WorkspaceScanSuggestion) => {
    setIsAdding(s.name);
    try {
      await addDomainTool(domainId, {
        name: s.name,
        description: s.description,
        type: s.type,
        example_usage: s.example_usage,
        parameters: s.parameters,
        code: s.code,
        executable: !!s.code,
        created_by: "ai",
      });
      setSuggestions((prev) => prev.filter((x) => x.name !== s.name));
      onMutate();
    } finally {
      setIsAdding(null);
    }
  };

  if (suggestions.length > 0) {
    return (
      <div className="space-y-3 w-full">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-grey">
            Workspace Scan Suggestions (review & approve)
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs"
            onClick={() => setSuggestions([])}
          >
            Dismiss
          </Button>
        </div>
        {suggestions.map((s) => (
          <div
            key={s.name}
            className="rounded-xl border border-dashed border-muted-teal/40 bg-muted-teal/5 p-4 space-y-2"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-blackberry text-sm">
                  {s.name}
                </span>
                <span className="bg-wheat/20 text-blackberry rounded-full text-xs px-2 py-0.5">
                  {s.type}
                </span>
                {s.code && (
                  <span className="bg-muted-teal/20 text-muted-teal rounded-full text-xs px-2 py-0.5">
                    executable
                  </span>
                )}
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleApprove(s)}
                disabled={isAdding === s.name}
              >
                {isAdding === s.name ? "Adding…" : "Approve"}
              </Button>
            </div>
            <p className="text-grey text-xs">{s.description}</p>
            {s.code && (
              <pre className="text-[10px] font-mono bg-blackberry/5 rounded-lg text-blackberry p-2 max-h-[120px] overflow-auto whitespace-pre-wrap">
                {s.code}
              </pre>
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleScan}
      disabled={isScanning}
    >
      {isScanning ? "Scanning…" : "🔍 Scan Workspace"}
    </Button>
  );
}
