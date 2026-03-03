import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export function activate(context: vscode.ExtensionContext) {

    const cmd = vscode.commands.registerCommand('resolvedpdf.convert', async (uri: vscode.Uri) => {

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
            vscode.window.showErrorMessage(
                'ResolvedPDF: Converter script not found. Please reinstall the extension.'
            );
            return;
        }

        const outputPath = inputPath.replace(/\.resolved$/, '.pdf');

        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: `ResolvedPDF: Converting ${path.basename(inputPath)}…`,
                cancellable: false,
            },
            () => new Promise<void>((resolve) => {

                const proc = cp.spawn('python', [scriptPath, inputPath, outputPath], {
                    cwd: path.dirname(inputPath),
                });

                let stderr = '';
                proc.stderr.on('data', (d: Buffer) => (stderr += d.toString()));

                proc.on('close', (code: number) => {
                    resolve();
                    if (code === 0 && fs.existsSync(outputPath)) {
                        vscode.window
                            .showInformationMessage(
                                `✅ PDF saved: ${path.basename(outputPath)}`,
                                'Open PDF',
                                'Show in Explorer'
                            )
                            .then((choice) => {
                                if (choice === 'Open PDF') {
                                    vscode.env.openExternal(vscode.Uri.file(outputPath));
                                } else if (choice === 'Show in Explorer') {
                                    vscode.commands.executeCommand(
                                        'revealFileInOS',
                                        vscode.Uri.file(outputPath)
                                    );
                                }
                            });
                    } else {
                        vscode.window.showErrorMessage(
                            `ResolvedPDF: Conversion failed.\n${stderr || 'Unknown error'}`
                        );
                    }
                });

                proc.on('error', (err: Error) => {
                    resolve();
                    if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
                        vscode.window.showErrorMessage(
                            'ResolvedPDF: Python not found. Please install Python 3 and add it to PATH.'
                        );
                    } else {
                        vscode.window.showErrorMessage(`ResolvedPDF: ${err.message}`);
                    }
                });
            })
        );
    });

    context.subscriptions.push(cmd);
}

export function deactivate() { }
