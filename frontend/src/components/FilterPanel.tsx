import { Category, ChatFilters, Department } from "../api/client";

interface FilterPanelProps {
  filters: ChatFilters;
  onFiltersChange: (filters: ChatFilters) => void;
  allowedDepartments: Department[];
}

const categories: Category[] = ["policy", "guide", "faq", "incident", "release_notes"];

export function FilterPanel({
  filters,
  onFiltersChange,
  allowedDepartments,
}: FilterPanelProps) {
  // Trial Phase: Removed Hybrid/Vector buttons (moved to chat header)
  // Changed: Default option to "Select", PascalCase formatting, label colors to black, font-weight to medium
  // Removed duplicate "Filters" header in modal (handled by filter-modal-header)
  return (
    <aside className="side-panel">

      <label className="filter-label">
        <span>Department</span>
        <select
          value={filters.department ?? ""}
          onChange={(event) =>
            onFiltersChange({ ...filters, department: (event.target.value || undefined) as Department | undefined })
          }
          className="filter-select"
        >
          <option value="">Select</option>
          {allowedDepartments.map((department) => (
            <option key={department} value={department}>
              {department.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ")}
            </option>
          ))}
        </select>
      </label>

      <label className="filter-label">
        <span>Category</span>
        <select
          value={filters.category ?? ""}
          onChange={(event) =>
            onFiltersChange({ ...filters, category: (event.target.value || undefined) as Category | undefined })
          }
          className="filter-select"
        >
          <option value="">Select</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ")}
            </option>
          ))}
        </select>
      </label>

      {/* Year field with calendar icon support */}
      <label className="filter-label">
        <span>Year</span>
        <input
          inputMode="numeric"
          type="number"
          placeholder="2026"
          value={filters.year ?? ""}
          onChange={(event) =>
            onFiltersChange({ ...filters, year: event.target.value ? Number(event.target.value) : undefined })
          }
          className="filter-input"
        />
      </label>
    </aside>
  );
}
