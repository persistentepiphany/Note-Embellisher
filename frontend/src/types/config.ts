export interface ProcessingConfig {
  add_bullet_points: boolean;
  add_headers: boolean;
  expand: boolean;
  summarize: boolean;
}

export const defaultConfig: ProcessingConfig = {
  add_bullet_points: false,
  add_headers: false,
  expand: false,
  summarize: false,
};