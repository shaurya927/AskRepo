export const languageColors: Record<string, string> = {
  Python: '#3572A5',
  JavaScript: '#f1e05a',
  TypeScript: '#3178c6',
  Java: '#b07219',
  'C++': '#f34b7d',
  Go: '#00ADD8',
  Rust: '#dea584',
  Ruby: '#701516',
  PHP: '#4F5D95',
  'C#': '#178600',
  HTML: '#e34c26',
  CSS: '#563d7c',
  Shell: '#89e051',
  Vue: '#41b883',
  Svelte: '#ff3e00',
  Dockerfile: '#384d54',
  JSON: '#292929',
  Markdown: '#083fa1',
  YAML: '#cb171e',
}

export const getLanguageColor = (language: string | null): string => {
  if (!language) return '#8b949e' // default gray
  return languageColors[language] || '#8b949e'
}
