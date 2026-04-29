<template>
  <el-dialog
    v-model="visible"
    title="更换头像"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="avatar-upload-dialog">
      <!-- 上传区域 -->
      <div v-if="!selectedFile" class="upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
        <div class="upload-placeholder">
          <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="17 8 12 3 7 8" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="12" y1="3" x2="12" y2="15" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <div class="upload-text">点击或拖拽图片到此处上传</div>
          <div class="upload-hint">支持 JPG、PNG 格式，文件大小不超过 2MB</div>
        </div>
        <input
          ref="fileInput"
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          style="display: none"
          @change="handleFileSelect"
        />
      </div>

      <!-- 预览和裁剪区域 -->
      <div v-else class="preview-area">
        <div class="preview-header">
          <span class="preview-title">预览</span>
          <el-button type="text" size="small" @click="resetFile">重新选择</el-button>
        </div>

        <div class="crop-container">
          <div class="crop-wrapper">
            <img
              ref="imageRef"
              :src="imageUrl"
              class="crop-image"
              alt="头像预览"
              @load="onImageLoad"
            />
          </div>
          <div class="crop-preview-box">
            <div class="preview-label">裁剪预览</div>
            <div class="preview-canvas-wrapper">
              <canvas ref="previewCanvas" width="200" height="200"></canvas>
            </div>
          </div>
        </div>

        <div class="crop-controls">
          <div class="control-group">
            <span class="control-label">缩放</span>
            <el-slider v-model="zoom" :min="0.5" :max="3" :step="0.1" class="zoom-slider" />
          </div>
          <div class="control-group">
            <span class="control-label">旋转</span>
            <div class="rotate-buttons">
              <el-button size="small" @click="rotate(-90)">
                <svg class="rotate-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 12a9 9 0 109-9 9.75 9.75 0 00-6.74 2.74L3 8" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M3 3v5h5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </el-button>
              <el-button size="small" @click="rotate(90)">
                <svg class="rotate-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 12a9 9 0 11-9-9 9.75 9.75 0 016.74 2.74L21 8" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M21 3v5h-5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 进度条 -->
      <div v-if="uploading" class="progress-container">
        <el-progress :percentage="uploadProgress" :stroke-width="4" />
        <div class="progress-text">上传中...</div>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button
        v-if="selectedFile"
        type="primary"
        @click="handleUpload"
        :loading="uploading"
        :disabled="!canCrop"
      >
        确认上传
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const props = defineProps({
  modelValue: Boolean,
  currentAvatar: String
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const fileInput = ref(null)
const imageRef = ref(null)
const previewCanvas = ref(null)

const selectedFile = ref(null)
const imageUrl = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const canCrop = ref(false)

// 裁剪参数
const zoom = ref(1)
const rotation = ref(0)
const cropBox = ref({
  x: 0,
  y: 0,
  size: 200
})

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    validateAndLoadFile(file)
  }
}

// 处理拖拽上传
const handleDrop = (e) => {
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    validateAndLoadFile(file)
  }
}

// 验证并加载文件
const validateAndLoadFile = (file) => {
  // 检查文件类型
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!validTypes.includes(file.type)) {
    ElMessage.error('请选择 JPG、PNG、GIF 或 WebP 格式的图片')
    return
  }

  // 检查文件大小（2MB）
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 2MB')
    return
  }

  selectedFile.value = file
  imageUrl.value = URL.createObjectURL(file)
}

// 重置文件选择
const resetFile = () => {
  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value)
  }
  selectedFile.value = null
  imageUrl.value = null
  canCrop.value = false
  fileInput.value.value = ''
}

// 图片加载完成
const onImageLoad = async () => {
  await nextTick()
  canCrop.value = true
  updatePreview()
}

// 旋转图片
const rotate = (degrees) => {
  rotation.value = (rotation.value + degrees) % 360
  updatePreview()
}

// 更新裁剪预览
const updatePreview = () => {
  if (!imageRef.value || !previewCanvas.value) return

  const canvas = previewCanvas.value
  const ctx = canvas.getContext('2d')
  const img = imageRef.value

  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // 计算缩放后的尺寸
  const scale = zoom.value
  const rotated = rotation.value % 180 !== 0

  // 保存状态
  ctx.save()

  // 移动到画布中心
  ctx.translate(canvas.width / 2, canvas.height / 2)

  // 旋转
  ctx.rotate((rotation.value * Math.PI) / 180)

  // 缩放
  ctx.scale(scale, scale)

  // 绘制图片（居中）
  const drawWidth = rotated ? img.height : img.width
  const drawHeight = rotated ? img.width : img.height

  ctx.drawImage(
    img,
    -drawWidth / 2,
    -drawHeight / 2,
    drawWidth,
    drawHeight
  )

  // 恢复状态
  ctx.restore()

  // 绘制裁剪框（圆形）
  ctx.save()
  ctx.beginPath()
  ctx.arc(canvas.width / 2, canvas.height / 2, 100, 0, Math.PI * 2)
  ctx.strokeStyle = '#3b82f6'
  ctx.lineWidth = 2
  ctx.stroke()
  ctx.restore()
}

// 监听缩放变化
watch(zoom, () => {
  updatePreview()
})

// 上传头像
const handleUpload = async () => {
  if (!selectedFile.value || !previewCanvas.value) return

  uploading.value = true
  uploadProgress.value = 0

  try {
    // 从预览画布获取裁剪后的图片
    const canvas = previewCanvas.value
    const blob = await new Promise((resolve) => {
      canvas.toBlob(resolve, 'image/jpeg', 0.9)
    })

    // 创建文件对象
    const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' })

    // 上传
    const result = await api.profile.uploadAvatar(file, (percent) => {
      uploadProgress.value = percent
    })

    if (result.success) {
      ElMessage.success('头像上传成功')
      emit('success', result.data.avatar_url)
      visible.value = false
    }
  } catch (error) {
    console.error('上传头像失败:', error)
    const message = error.detail?.message || error.message || '上传失败'
    ElMessage.error(message)
  } finally {
    uploading.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  resetFile()
  visible.value = false
}
</script>

<style scoped>
.avatar-upload-dialog {
  padding: 8px 0;
}

/* 上传区域 */
.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #f9fafb;
}

.upload-area:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.upload-icon {
  width: 64px;
  height: 64px;
  color: #9ca3af;
}

.upload-area:hover .upload-icon {
  color: #3b82f6;
}

.upload-text {
  font-size: 16px;
  color: #374151;
  font-weight: 500;
}

.upload-hint {
  font-size: 13px;
  color: #9ca3af;
}

/* 预览区域 */
.preview-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

/* 裁剪容器 */
.crop-container {
  display: flex;
  gap: 24px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
}

.crop-wrapper {
  flex: 1;
  max-height: 300px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.crop-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

/* 裁剪预览 */
.crop-preview-box {
  width: 200px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-label {
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}

.preview-canvas-wrapper {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
  background: #ffffff;
}

.preview-canvas-wrapper canvas {
  width: 100%;
  height: 100%;
}

/* 控制区域 */
.crop-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-label {
  width: 50px;
  font-size: 14px;
  color: #6b7280;
}

.zoom-slider {
  flex: 1;
}

.rotate-buttons {
  display: flex;
  gap: 8px;
}

.rotate-icon {
  width: 18px;
  height: 18px;
}

/* 进度条 */
.progress-container {
  padding: 16px;
  text-align: center;
}

.progress-text {
  margin-top: 8px;
  font-size: 14px;
  color: #6b7280;
}
</style>
