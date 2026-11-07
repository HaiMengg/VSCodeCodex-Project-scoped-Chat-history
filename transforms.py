"""Exact transformations for the supported Codex extension build."""
import hashlib

def digest(data):
    return hashlib.sha256(data).hexdigest()

VERSION = '26.1021.22027'

SETTING = 'chatgpt.historyCurrentWorkspaceOnly'

META_OLD = 'webviewMetaTags(e){let r=[],n=this.findPanelByWebview(e);'

META_NEW = 'webviewMetaTags(e){let r=[],n=this.findPanelByWebview(e);\n/* codex-workspace-history-patch-v2 */\nr.push(`<meta name="codex-workspace-history-roots" content="${yf(JSON.stringify(require("vscode").workspace.getConfiguration("chatgpt").get("historyCurrentWorkspaceOnly",true)?fv():[]))}">`);\n'

MATCH = 'workspaceHistoryMatches(e){\nlet meta=globalThis.document?.querySelector(\'meta[name="codex-workspace-history-roots"]\');\nif(!meta)return true;\nlet roots;try{roots=JSON.parse(meta.content)}catch{return true}\nif(!Array.isArray(roots)||roots.length===0)return true;\nlet norm=p=>{let s=String(p??\'\').replace(/\\\\/g,\'/\').replace(/\\/+$/,\'\');return /^[a-z]:\\//i.test(s)||s.startsWith(\'//\')?s.toLowerCase():s};\nlet cwd=norm(e.cwd);return cwd.length>0&&roots.some(root=>norm(root)===cwd);\n}'

UI_REPLACEMENTS = [('shouldSurfaceRecentConversation(e){return', 'workspaceHistoryMatches(e){\nlet meta=globalThis.document?.querySelector(\'meta[name="codex-workspace-history-roots"]\');\nif(!meta)return true;\nlet roots;try{roots=JSON.parse(meta.content)}catch{return true}\nif(!Array.isArray(roots)||roots.length===0)return true;\nlet norm=p=>{let s=String(p??\'\').replace(/\\\\/g,\'/\').replace(/\\/+$/,\'\');return /^[a-z]:\\//i.test(s)||s.startsWith(\'//\')?s.toLowerCase():s};\nlet cwd=norm(e.cwd);return cwd.length>0&&roots.some(root=>norm(root)===cwd);\n}shouldSurfaceRecentConversation(e){return this.workspaceHistoryMatches(e)&&'), ('shouldSurfaceThreadSummary(e){return', 'shouldSurfaceThreadSummary(e){return this.workspaceHistoryMatches(e)&&'), ('getThreadSummaries(){return this.threadSummaries}', 'getThreadSummaries(){return this.threadSummaries.filter(e=>this.workspaceHistoryMatches(e))}')]

HELPER = 'function codexWorkspaceHistoryVisible(e){\nlet meta=globalThis.document?.querySelector(\'meta[name="codex-workspace-history-roots"]\');\nif(!meta)return true;\nlet roots;try{roots=JSON.parse(meta.content)}catch{return true}\nif(!Array.isArray(roots)||roots.length===0)return true;\nlet norm=p=>{let s=String(p??\'\').replace(/\\\\/g,\'/\').replace(/\\/+$/,\'\');return /^[a-z]:\\//i.test(s)||s.startsWith(\'//\')?s.toLowerCase():s};\nlet cwd=norm(e.cwd);return cwd.length>0&&roots.some(root=>norm(root)===cwd);\n}'

RECENT = 'field:`recentThreads`,listener:n}),r=>{en(t,()=>{'

RECENT_NEW = 'field:`recentThreads`,listener:n}),r=>{r=r.filter(row=>codexWorkspaceHistoryVisible(row.summary));en(t,()=>{'

TOP = 'Wj=j(F,(e,{get:t})=>t(Vj,e).topLevel,{isEqual:Aa})'

TOP_NEW = 'Wj=j(F,(e,{get:t})=>t(Vj,e).topLevel.filter(id=>{let summary=t(Kj,{hostId:e,conversationId:id});return summary!=null&&codexWorkspaceHistoryVisible(summary)}),{isEqual:Aa})'
