import { MoreHorizontal, Star, Share2, Download, Calendar, FileText } from "lucide-react";
import { Card, CardContent, CardHeader } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";

interface ProjectCardProps {
  id: string;
  title: string;
  description: string;
  category: string;
  lastModified: string;
  pageCount: number;
  isFavorite?: boolean;
  color?: string;
}

export function ProjectCard({
  title,
  description,
  category,
  lastModified,
  pageCount,
  isFavorite = false,
  color = "bg-blue-500"
}: ProjectCardProps) {
  return (
    <Card className="group hover:shadow-lg transition-all duration-200 cursor-pointer">
      <CardHeader className="p-4 pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 ${color} rounded-lg flex items-center justify-center`}>
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div>
              <Badge variant="secondary" className="text-xs">
                {category}
              </Badge>
            </div>
          </div>
          <div className="flex space-x-1">
            <Button
              variant="ghost"
              size="icon"
              className="w-8 h-8"
            >
              <Star className={`w-4 h-4 ${isFavorite ? 'text-yellow-500 fill-yellow-500' : 'text-gray-600'}`} />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="w-8 h-8"
                >
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <Share2 className="w-4 h-4 mr-2" />
                  Share
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </DropdownMenuItem>
                <DropdownMenuItem className="text-destructive">
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-0">
        <h3 className="font-medium mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
          {description}
        </p>
        
        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
          <div className="flex items-center space-x-1">
            <FileText className="w-3 h-3" />
            <span>{pageCount} pages</span>
          </div>
          <div className="flex items-center space-x-1">
            <Calendar className="w-3 h-3" />
            <span>{lastModified}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}