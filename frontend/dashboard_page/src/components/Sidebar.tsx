import { Home, FolderOpen, Star, Archive, Settings, Plus, FileText, Tag, Calendar } from "lucide-react";
import { Button } from "./ui/button";
import { Separator } from "./ui/separator";

const navigationItems = [
  { icon: Home, label: "Dashboard", active: true },
  { icon: FolderOpen, label: "All Projects", count: 0 },
  { icon: Star, label: "Favorites", count: 0 },
  { icon: Calendar, label: "Recent", count: 0 },
  { icon: Archive, label: "Archived", count: 0 },
];

const categories = [
  { icon: FileText, label: "Text Notes", count: 0 },
  { icon: Tag, label: "Quick Notes", count: 0 },
  { icon: FolderOpen, label: "Research", count: 0 },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-sidebar border-r border-sidebar-border h-[calc(100vh-4rem)] overflow-y-auto">
      <div className="p-4">
        {/* Quick Actions */}
        <div className="mb-6">
          <Button className="w-full justify-start" size="sm">
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>

        {/* Navigation */}
        <nav className="space-y-1 mb-6">
          {navigationItems.map((item) => (
            <Button
              key={item.label}
              variant={item.active ? "secondary" : "ghost"}
              className="w-full justify-start"
              size="sm"
            >
              <item.icon className="w-4 h-4 mr-3" />
              <span className="flex-1 text-left">{item.label}</span>
              {item.count !== undefined && (
                <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                  {item.count}
                </span>
              )}
            </Button>
          ))}
        </nav>

        <Separator className="my-4" />

        {/* Categories */}
        <div>
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
            Categories
          </h3>
          <nav className="space-y-1">
            {categories.map((category) => (
              <Button
                key={category.label}
                variant="ghost"
                className="w-full justify-start"
                size="sm"
              >
                <category.icon className="w-4 h-4 mr-3" />
                <span className="flex-1 text-left">{category.label}</span>
                <span className="text-xs text-muted-foreground">
                  {category.count}
                </span>
              </Button>
            ))}
          </nav>
        </div>

        <Separator className="my-4" />

        {/* Settings */}
        <Button variant="ghost" className="w-full justify-start" size="sm">
          <Settings className="w-4 h-4 mr-3" />
          Settings
        </Button>
      </div>
    </aside>
  );
}