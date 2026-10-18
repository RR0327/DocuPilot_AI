export function isTerminal(state) { return ['succeeded', 'failed'].includes(state); }
export function nextPoll(state) { return isTerminal(state) ? 0 : 2000; }
