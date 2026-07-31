import { Link } from "react-router-dom";

export interface BreadcrumbItem {
  label: string;
  to?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export default function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-slate-400">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        if (isLast || !item.to) {
          return (
            <span key={item.label} className="text-slate-200" aria-current="page">
              {item.label}
            </span>
          );
        }
        return (
          <span key={item.label} className="flex items-center gap-1.5">
            <Link to={item.to} className="hover:text-white transition-colors">
              {item.label}
            </Link>
            <span>/</span>
          </span>
        );
      })}
    </nav>
  );
}
