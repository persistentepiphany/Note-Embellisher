import { Plus, Upload, FileText, FolderPlus } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";

interface EmptyStateProps {
  type: "projects" | "folders" | "favorites" | "recent";
}

export function EmptyState({ type }: EmptyStateProps) {
  const getEmptyStateContent = () => {
    switch (type) {
      case "projects":
        return {
          icon: FileText,
          title: "No projects yet",
          description: "Start creating your first note project to organize your thoughts and ideas",
          primaryAction: "Create New Project",
          secondaryAction: "Import Project"
        };
      case "folders":
        return {
          icon: FolderPlus,
          title: "No folders created",
          description: "Create subject folders to organize your projects by topics like Biology, Math, or Computer Science",
          primaryAction: "Create New Folder",
          secondaryAction: null
        };
      case "favorites":
        return {
          icon: FileText,
          title: "No favorite projects",
          description: "Star projects you frequently use to see them here for quick access",
          primaryAction: "Browse All Projects",
          secondaryAction: null
        };
      case "recent":
        return {
          icon: FileText,
          title: "No recent activity",
          description: "Your recently opened projects will appear here for easy access",
          primaryAction: "Create New Project",
          secondaryAction: null
        };
    }
  };

  const content = getEmptyStateContent();
  const IconComponent = content.icon;

  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Card className="w-full max-w-md mx-auto">
        <CardContent className="flex flex-col items-center justify-center p-8 text-center">
          <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
            <IconComponent className="w-8 h-8 text-muted-foreground" />
          </div>
          
          <h3 className="mb-2">{content.title}</h3>
          <p className="text-muted-foreground mb-6 max-w-sm">
            {content.description}
          </p>
          
          <div className="flex flex-col sm:flex-row gap-3 w-full">
            <Button className="flex-1">
              <Plus className="w-4 h-4 mr-2" />
              {content.primaryAction}
            </Button>
            {content.secondaryAction && (
              <Button variant="outline" className="flex-1">
                <Upload className="w-4 h-4 mr-2" />
                {content.secondaryAction}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}