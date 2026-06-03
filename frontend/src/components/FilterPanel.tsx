import { Category, ChatFilters, Department, RetrievalMode } from "../api/client";

interface FilterPanelProps {
  filters: ChatFilters;
  retrievalMode: RetrievalMode;
  onFiltersChange: (filters: ChatFilters) => void;
  onRetrievalModeChange: (mode: RetrievalMode) => void;
  allowedDepartments: Department[];
}

const categories: Category[] = ["policy", "guide", "faq", "incident", "release_notes"];

export function FilterPanel({
  filters,
  retrievalMode,
  onFiltersChange,
  onRetrievalModeChange,
  allowedDepartments,
}: FilterPanelProps) {
  return (
    <aside className="side-panel">
      <div className="panel-header">
        <h2>Filters</h2>
      </div>

      <label>
        Department
        <select
          value={filters.department ?? ""}
          onChange={(event) =>
            onFiltersChange({ ...filters, department: (event.target.value || undefined) as Department | undefined })
          }
        >
          <option value="">Allowed departments</option>
          {allowedDepartments.map((department) => (
            <option key={department} value={department}>
              {department.replace("_", " ")}
            </option>
          ))}
        </select>
      </label>

      <label>
        Category
        <select
          value={filters.category ?? ""}
          onChange={(event) =>
            onFiltersChange({ ...filters, category: (event.target.value || undefined) as Category | undefined })
          }
        >
          <option value="">Any category</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category.replace("_", " ")}
            </option>
          ))}
        </select>
      </label>

      <label>
        Year
        <input
          inputMode="numeric"
          placeholder="2026"
          value={filters.year ?? ""}
          onChange={(event) =>
            onFiltersChange({ ...filters, year: event.target.value ? Number(event.target.value) : undefined })
          }
        />
      </label>

      <div className="segmented-control">
        <button className={retrievalMode === "hybrid" ? "active" : ""} onClick={() => onRetrievalModeChange("hybrid")}>
          Hybrid
        </button>
        <button className={retrievalMode === "vector" ? "active" : ""} onClick={() => onRetrievalModeChange("vector")}>
          Vector
        </button>
      </div>
    </aside>
  );
}
