import { MoreHorizontal, Folder, Calendar } from "lucide-react";
import { Card, CardContent, CardHeader } from "./ui/card";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";

interface FolderCardProps {
  id: string;
  name: string;
  description: string;
  projectCount: number;
  lastModified: string;
  color: string;
}

export function FolderCard({
  name,
  description,
  projectCount,
  lastModified,
  color
}: FolderCardProps) {
  return (
    <Card className="group hover:shadow-lg transition-all duration-200 cursor-pointer">
      <CardHeader className="p-4 pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center`}>
              <Folder className="w-6 h-6 text-white" />
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="w-8 h-8 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                Open Folder
              </DropdownMenuItem>
              <DropdownMenuItem>
                Rename
              </DropdownMenuItem>
              <DropdownMenuItem className="text-destructive">
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-0">
        <h3 className="font-medium mb-2">{name}</h3>
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
          {description}
        </p>
        
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{projectCount} projects</span>
          <div className="flex items-center space-x-1">
            <Calendar className="w-3 h-3" />
            <span>{lastModified}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}