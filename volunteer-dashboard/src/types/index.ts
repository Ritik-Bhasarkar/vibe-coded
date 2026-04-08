// src/types/index.ts

export type OpportunityResult = {
  title: string;
  snippet: string;
  link: string;
  displayUrl: string;
};

export type SearchParams = {
  location: string;
  category?: string;
  platform?: string;
  hostelsOnly?: boolean;
};

export type SearchResponse = {
  results: OpportunityResult[];
};

export type SearchError = {
  error: string;
};
