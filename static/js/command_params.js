/**
 * コマンドパラメーター管理モジュール
 * パラメーター設定の操作と管理を担当
 */

// グローバル変数
let currentDeviceId = '';
let currentParameters = null;
let boundFileName = null;

// DOM要素取得関数
function getParamElement(id) {
    return document.getElementById(id);
}

// コマンドパラメーター関連の初期化
document.addEventListener('DOMContentLoaded', () => {
    setupCommandParamsListeners();
});

/**
 * コマンドパラメーター関連のイベントリスナーを設定
 */
function setupCommandParamsListeners() {
    // デバイスIDを含むパスのプレビュー
    const storageSubDir = getParamElement('param-storage-sub-dir');
    const storageSubDirIR = getParamElement('param-storage-sub-dir-ir');
    const commandParamsDeviceId = getParamElement('command-params-device-id');
    
    if (storageSubDir && storageSubDirIR && commandParamsDeviceId) {
        // 入力時のプレビュー更新
        [storageSubDir, storageSubDirIR].forEach(elem => {
            elem.addEventListener('input', () => {
                updatePathPreview(elem);
            });
        });
        
        // デバイスIDが変更されたときのプレビュー更新
        const observer = new MutationObserver(() => {
            updatePathPreview(storageSubDir);
            updatePathPreview(storageSubDirIR);
        });
        
        observer.observe(commandParamsDeviceId, { attributes: true });
    }
    
    // モード切り替えによる表示制御は削除（常に全項目表示する）
}

/**
 * パスプレビューを更新
 * @param {HTMLInputElement} inputElem - 入力要素
 */
function updatePathPreview(inputElem) {
    const deviceId = getParamElement('command-params-device-id').value;
    const path = inputElem.value;
    
    if (deviceId && path.includes('{device_id}')) {
        // デバイスIDからサフィックスを抽出
        const deviceSuffix = deviceId.split('-').pop();
        
        // プレビューでは完全なデバイスIDではなくサフィックスを使用
        const previewPath = path.replace('{device_id}', deviceSuffix);
        inputElem.title = `実際のパス: ${previewPath}`;
    } else {
        inputElem.title = '';
    }
}

/**
 * コマンドパラメーターのバリデーション
 * @returns {boolean} バリデーション結果
 */
function validateCommandParameters() {
    let isValid = true;
    
    // 基本パラメーターのバリデーション
    const mode = parseInt(getParamElement('param-mode').value);
    if (isNaN(mode) || mode < 0 || mode > 2) {
        isValid = false;
        showToast('Modeの値が無効です', 'error');
    }
    
    // モードに応じて必須項目をチェック
    if ((mode === 0 || mode === 1) && !getParamElement('param-storage-name').value) {
        isValid = false;
        showToast('StorageNameを入力してください', 'error');
    }
    
    if ((mode === 1 || mode === 2) && !getParamElement('param-storage-name-ir').value) {
        isValid = false;
        showToast('StorageNameIRを入力してください', 'error');
    }
    
    // 数値フィールドのバリデーション
    const numericFields = [
        { id: 'param-crop-h-offset', min: 0, max: 4055 },
        { id: 'param-crop-v-offset', min: 0, max: 3039 },
        { id: 'param-crop-h-size', min: 0, max: 4056 },
        { id: 'param-crop-v-size', min: 0, max: 3040 },
        { id: 'param-num-images', min: 0, max: 10000 },
        { id: 'param-upload-interval', min: 1, max: 2592000 },
        { id: 'param-num-inferences', min: 1, max: 100 },
        { id: 'param-max-detections', min: 1, max: 100 },
        { id: 'param-threshold', min: 0.01, max: 0.99 },
        { id: 'param-input-width', min: 1, max: 10000 },
        { id: 'param-input-height', min: 1, max: 10000 }
    ];
    
    for (const field of numericFields) {
        const element = getParamElement(field.id);
        if (!element) continue;
        
        const value = field.id === 'param-threshold' ? 
            parseFloat(element.value) : parseInt(element.value);
        
        if (isNaN(value) || value < field.min || value > field.max) {
            isValid = false;
            const fieldName = element.previousElementSibling ? 
                element.previousElementSibling.textContent.replace(':', '') : field.id;
            showToast(`${fieldName}の値が無効です (${field.min}〜${field.max})`, 'error');
            break;
        }
    }
    
    return isValid;
}

/**
 * コマンドパラメーターを適用する前の確認
 * @returns {boolean} 適用可能かどうか
 */
function confirmApplyParameters() {
    // パラメーターをバリデーション
    if (!validateCommandParameters()) {
        return false;
    }
    
    // 確認ダイアログを表示
    return confirm('コマンドパラメーターをデバイスに適用しますか？\n(推論を一時停止して適用します)');
}

/**
 * コマンドパラメーターを読み込む
 * @param {string} deviceId - デバイスID
 */
function loadCommandParameters(deviceId) {
    console.log(`Loading command parameters for device: ${deviceId}`);
    
    if (!deviceId) {
        console.error('Device ID is empty');
        showToast('デバイスIDが設定されていません', 'error');
        return;
    }
    
    currentDeviceId = deviceId;
    
    // 読み込み中表示
    const applyParamsBtn = getParamElement('apply-params-btn');
    const resetParamsBtn = getParamElement('reset-params-btn');
    
    if (applyParamsBtn) {
        applyParamsBtn.disabled = true;
        applyParamsBtn.textContent = '読み込み中...';
    }
    
    if (resetParamsBtn) {
        resetParamsBtn.disabled = true;
    }
    
    // API呼び出し
    fetch(`/api/command_parameters/${deviceId}`)
        .then(response => response.json())
        .then(data => {
            console.log('Command parameters loaded:', data);
            
            // バインド状態を確認
            if (data.success) {
                // パラメーターが存在するかチェック (bound_file が存在するか)
                if (data.bound_file) {
                    boundFileName = data.bound_file;
                    
                    // バインドされている場合は編集可能にする
                    if (applyParamsBtn) {
                        applyParamsBtn.disabled = false;
                        applyParamsBtn.textContent = 'デバイスに適用';
                    }
                    
                    if (resetParamsBtn) {
                        resetParamsBtn.disabled = false;
                    }
                    
                    // パラメーターをフォームに設定
                    setCommandParametersToForm(data.parameters);
                    currentParameters = data.parameters;
                    
                    // バインドファイル名を表示
                    const boundFileInfo = getParamElement('bound-file-info');
                    if (boundFileInfo) {
                        boundFileInfo.textContent = `バインドされているファイル: ${data.bound_file}`;
                        boundFileInfo.style.display = 'block';
                    }
                    
                    // 結果表示をクリア
                    const paramsResult = getParamElement('params-result');
                    if (paramsResult) {
                        paramsResult.style.display = 'none';
                        paramsResult.className = 'connection-result';
                    }
                } else {
                    // バインドされていない場合はエラーメッセージを表示
                    if (applyParamsBtn) {
                        applyParamsBtn.disabled = true;
                    }
                    
                    if (resetParamsBtn) {
                        resetParamsBtn.disabled = true;
                    }
                    
                    const paramsResult = getParamElement('params-result');
                    if (paramsResult) {
                        paramsResult.textContent = 'コマンドパラメーターがバインドされていません。コンソールでバインドしてください。';
                        paramsResult.className = 'connection-result error';
                        paramsResult.style.display = 'block';
                    }
                    
                    // バインド情報をクリア
                    const boundFileInfo = getParamElement('bound-file-info');
                    if (boundFileInfo) {
                        boundFileInfo.textContent = '';
                        boundFileInfo.style.display = 'none';
                    }
                    
                    showToast('コマンドパラメーターがバインドされていません', 'error');
                }
            } else {
                if (applyParamsBtn) {
                    applyParamsBtn.disabled = true;
                }
                
                if (resetParamsBtn) {
                    resetParamsBtn.disabled = true;
                }
                
                showToast(data.message || 'パラメーター取得に失敗しました', 'error');
                
                const paramsResult = getParamElement('params-result');
                if (paramsResult) {
                    paramsResult.textContent = data.message || 'パラメーター取得に失敗しました';
                    paramsResult.className = 'connection-result error';
                    paramsResult.style.display = 'block';
                }
            }
        })
        .catch(error => {
            console.error('Error fetching command parameters:', error);
            showToast('パラメーター取得中にエラーが発生しました', 'error');
            
            // ボタンを無効化
            if (applyParamsBtn) {
                applyParamsBtn.disabled = true;
            }
            
            if (resetParamsBtn) {
                resetParamsBtn.disabled = true;
            }
        });
}

/**
 * コマンドパラメーターをフォームに設定
 * @param {Object} parameters - パラメーターオブジェクト
 */
function setCommandParametersToForm(parameters) {
    try {
        console.log('Setting command parameters to form:', parameters);
        
        // StartUploadInferenceDataコマンドのパラメーターを取得
        const commands = parameters.commands || [];
        const commandParams = commands.find(cmd => cmd.command_name === 'StartUploadInferenceData');
        
        if (!commandParams || !commandParams.parameters) {
            console.error('No valid parameters found');
            return;
        }
        
        const params = commandParams.parameters;
        
        // 基本パラメーター
        setFormValue('param-mode', params.Mode);
        
        // 画像アップロード設定 (常に表示)
        setFormValue('param-upload-method', params.UploadMethod);
        setFormValue('param-storage-name', params.StorageName);
        setFormValue('param-storage-sub-dir', params.StorageSubDirectoryPath);
        setFormValue('param-file-format', params.FileFormat);
        
        // 推論結果アップロード設定 (常に表示)
        setFormValue('param-upload-method-ir', params.UploadMethodIR);
        setFormValue('param-storage-name-ir', params.StorageNameIR);
        setFormValue('param-storage-sub-dir-ir', params.StorageSubDirectoryPathIR);
        
        // 画像切り抜き設定
        setFormValue('param-crop-h-offset', params.CropHOffset);
        setFormValue('param-crop-v-offset', params.CropVOffset);
        setFormValue('param-crop-h-size', params.CropHSize);
        setFormValue('param-crop-v-size', params.CropVSize);
        
        // アップロードパラメーター
        setFormValue('param-num-images', params.NumberOfImages);
        setFormValue('param-upload-interval', params.UploadInterval);
        setFormValue('param-num-inferences', params.NumberOfInferencesPerMessage);
        
        // PPLパラメーター
        if (params.PPLParameter) {
            setFormValue('param-max-detections', params.PPLParameter.max_detections);
            setFormValue('param-threshold', params.PPLParameter.threshold);
            setFormValue('param-input-width', params.PPLParameter.input_width);
            setFormValue('param-input-height', params.PPLParameter.input_height);
        }
        
        console.log('Command parameters set to form successfully');
    } catch (error) {
        console.error('Error setting command parameters to form:', error);
    }
}

/**
 * フォーム値を設定するヘルパー関数
 * @param {string} id - 要素ID
 * @param {any} value - 設定する値
 */
function setFormValue(id, value) {
    const element = getParamElement(id);
    if (element && value !== undefined) {
        element.value = value;
    }
}

/**
 * フォームからコマンドパラメーターを取得
 * @returns {Object} パラメーターオブジェクト
 */
function getCommandParametersFromForm() {
    try {
        const deviceId = getParamElement('command-params-device-id').value;
        
        if (!deviceId) {
            console.error('Device ID is empty');
            showToast('デバイスIDが設定されていません', 'error');
            return null;
        }
        
        // 基本パラメーター
        const mode = parseInt(getParamElement('param-mode').value);
        
        // 画像アップロード設定
        const uploadMethod = getParamElement('param-upload-method').value;
        const storageName = getParamElement('param-storage-name').value;
        const storageSubDir = getParamElement('param-storage-sub-dir').value;
        const fileFormat = getParamElement('param-file-format').value;
        
        // 推論結果アップロード設定
        const uploadMethodIR = getParamElement('param-upload-method-ir').value;
        const storageNameIR = getParamElement('param-storage-name-ir').value;
        const storageSubDirIR = getParamElement('param-storage-sub-dir-ir').value;
        
        // 画像切り抜き設定
        const cropHOffset = parseInt(getParamElement('param-crop-h-offset').value);
        const cropVOffset = parseInt(getParamElement('param-crop-v-offset').value);
        const cropHSize = parseInt(getParamElement('param-crop-h-size').value);
        const cropVSize = parseInt(getParamElement('param-crop-v-size').value);
        
        // アップロードパラメーター
        const numImages = parseInt(getParamElement('param-num-images').value);
        const uploadInterval = parseInt(getParamElement('param-upload-interval').value);
        const numInferences = parseInt(getParamElement('param-num-inferences').value);
        
        // PPLパラメーター
        const maxDetections = parseInt(getParamElement('param-max-detections').value);
        const threshold = parseFloat(getParamElement('param-threshold').value);
        const inputWidth = parseInt(getParamElement('param-input-width').value);
        const inputHeight = parseInt(getParamElement('param-input-height').value);
        
        // コマンドパラメーターを構築
        return {
            "commands": [
                {
                    "command_name": "StartUploadInferenceData",
                    "parameters": {
                        "Mode": mode,
                        "UploadMethod": uploadMethod,
                        "StorageName": storageName,
                        "StorageSubDirectoryPath": storageSubDir,
                        "FileFormat": fileFormat,
                        "UploadMethodIR": uploadMethodIR,
                        "StorageNameIR": storageNameIR,
                        "StorageSubDirectoryPathIR": storageSubDirIR,
                        "CropHOffset": cropHOffset,
                        "CropVOffset": cropVOffset,
                        "CropHSize": cropHSize,
                        "CropVSize": cropVSize,
                        "NumberOfImages": numImages,
                        "UploadInterval": uploadInterval,
                        "NumberOfInferencesPerMessage": numInferences,
                        "PPLParameter": {
                            "header": {
                                "id": "00",
                                "version": "01.01.00"
                            },
                            "dnn_output_detections": 100,
                            "max_detections": maxDetections,
                            "threshold": threshold,
                            "input_width": inputWidth,
                            "input_height": inputHeight
                        }
                    }
                }
            ]
        };
    } catch (error) {
        console.error('Error getting command parameters from form:', error);
        showToast('パラメーターの取得に失敗しました', 'error');
        return null;
    }
}

/**
 * コマンドパラメーターを適用
 */
function applyCommandParameters() {
    console.log('Applying command parameters...');
    
    // デバイスIDを取得
    const deviceId = getParamElement('command-params-device-id').value;
    
    if (!deviceId) {
        showToast('デバイスIDが設定されていません', 'error');
        return;
    }
    
    // バリデーション
    if (!validateCommandParameters()) {
        return;
    }
    
    // 確認ダイアログを表示
    if (!confirm('コマンドパラメーターをデバイスに適用しますか？\n(推論を一時停止して適用します)')) {
        return;
    }
    
    // パラメーターを取得
    const parameters = getCommandParametersFromForm();
    
    if (!parameters) {
        showToast('パラメーターの取得に失敗しました', 'error');
        return;
    }
    
    console.log('Applying parameters to device:', deviceId, parameters);
    
    // ボタンを無効化
    const applyParamsBtn = getParamElement('apply-params-btn');
    const resetParamsBtn = getParamElement('reset-params-btn');
    
    if (applyParamsBtn) {
        applyParamsBtn.disabled = true;
        applyParamsBtn.textContent = '適用中...';
    }
    
    if (resetParamsBtn) {
        resetParamsBtn.disabled = true;
    }
    
    // 結果表示をリセット
    const paramsResult = getParamElement('params-result');
    if (paramsResult) {
        paramsResult.textContent = 'パラメーターを適用中...';
        paramsResult.className = 'connection-result';
        paramsResult.style.display = 'block';
    }
    
    // パラメーターを適用
    fetch(`/api/command_parameters/${deviceId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(parameters)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Apply parameters response:', data);
        
        // ボタンを有効化
        if (applyParamsBtn) {
            applyParamsBtn.disabled = false;
            applyParamsBtn.textContent = 'デバイスに適用';
        }
        
        if (resetParamsBtn) {
            resetParamsBtn.disabled = false;
        }
        
        if (data.success) {
            if (paramsResult) {
                paramsResult.textContent = data.message;
                paramsResult.className = 'connection-result success';
            }
            showToast(data.message, 'success');
            
            // 成功した場合は現在のパラメーターを更新
            currentParameters = parameters;
        } else {
            if (paramsResult) {
                paramsResult.textContent = data.message;
                paramsResult.className = 'connection-result error';
            }
            showToast(data.message || 'パラメーターの適用に失敗しました', 'error');
        }
    })
    .catch(error => {
        console.error('Error applying command parameters:', error);
        
        // ボタンを有効化
        if (applyParamsBtn) {
            applyParamsBtn.disabled = false;
            applyParamsBtn.textContent = 'デバイスに適用';
        }
        
        if (resetParamsBtn) {
            resetParamsBtn.disabled = false;
        }
        
        if (paramsResult) {
            paramsResult.textContent = 'パラメーターの適用中にエラーが発生しました';
            paramsResult.className = 'connection-result error';
        }
        
        showToast('パラメーターの適用中にエラーが発生しました', 'error');
    });
}

/**
 * パラメーターをリセット
 */
function resetParameters() {
    if (!currentParameters) {
        showToast('リセットするパラメーターがありません', 'error');
        return;
    }
    
    if (!confirm('パラメーターを取得時の値にリセットしますか？')) {
        return;
    }
    
    // 現在保存されているパラメーターをフォームに設定
    setCommandParametersToForm(currentParameters);
    
    // 結果表示をクリア
    const paramsResult = getParamElement('params-result');
    if (paramsResult) {
        paramsResult.style.display = 'none';
    }
    
    showToast('パラメーターをリセットしました', 'success');
}