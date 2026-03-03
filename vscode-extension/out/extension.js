"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const cp = __importStar(require("child_process"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
function activate(context) {
    const cmd = vscode.commands.registerCommand('resolvedpdf.convert', async (uri) => {
        // If triggered from command palette (no URI), use active editor
        if (!uri) {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('ResolvedPDF: No .resolved file is open.');
                return;
            }
            uri = editor.document.uri;
        }
        const inputPath = uri.fsPath;
        if (!inputPath.endsWith('.resolved')) {
            vscode.window.showErrorMessage('ResolvedPDF: Please select a .resolved file.');
            return;
        }
        if (!fs.existsSync(inputPath)) {
            vscode.window.showErrorMessage(`ResolvedPDF: File not found: ${inputPath}`);
            return;
        }
        // Find the converter script — shipped alongside the extension
        const scriptPath = path.join(context.extensionPath, 'scripts', 'convert_resolved.py');
        if (!fs.existsSync(scriptPath)) {
            vscode.window.showErrorMessage('ResolvedPDF: Converter script not found. Please reinstall the extension.');
            return;
        }
        const outputPath = inputPath.replace(/\.resolved$/, '.pdf');
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `ResolvedPDF: Converting ${path.basename(inputPath)}…`,
            cancellable: false,
        }, () => new Promise((resolve) => {
            const proc = cp.spawn('python', [scriptPath, inputPath, outputPath], {
                cwd: path.dirname(inputPath),
            });
            let stderr = '';
            proc.stderr.on('data', (d) => (stderr += d.toString()));
            proc.on('close', (code) => {
                resolve();
                if (code === 0 && fs.existsSync(outputPath)) {
                    vscode.window
                        .showInformationMessage(`✅ PDF saved: ${path.basename(outputPath)}`, 'Open PDF', 'Show in Explorer')
                        .then((choice) => {
                        if (choice === 'Open PDF') {
                            vscode.env.openExternal(vscode.Uri.file(outputPath));
                        }
                        else if (choice === 'Show in Explorer') {
                            vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(outputPath));
                        }
                    });
                }
                else {
                    vscode.window.showErrorMessage(`ResolvedPDF: Conversion failed.\n${stderr || 'Unknown error'}`);
                }
            });
            proc.on('error', (err) => {
                resolve();
                if (err.code === 'ENOENT') {
                    vscode.window.showErrorMessage('ResolvedPDF: Python not found. Please install Python 3 and add it to PATH.');
                }
                else {
                    vscode.window.showErrorMessage(`ResolvedPDF: ${err.message}`);
                }
            });
        }));
    });
    context.subscriptions.push(cmd);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map