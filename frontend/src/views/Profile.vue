<template>
  <div class="profile-page">
    <div class="profile-container">
      <!-- 用户信息卡片 -->
      <el-card class="profile-header-card">
        <div class="profile-header">
          <div class="avatar-section">
            <div class="avatar-wrapper">
              <el-avatar
                :src="profile.avatar_url || defaultAvatar"
                :size="120"
                shape="circle"
                class="user-avatar"
              >
                <span class="avatar-text">{{ avatarText }}</span>
              </el-avatar>
              <el-button
                v-if="isOwnProfile"
                class="edit-avatar-btn"
                circle
                size="small"
                @click="showEditAvatar = true"
              >
                <svg class="edit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </el-button>
            </div>
          </div>

          <div class="info-section">
            <div class="username-row">
              <h1 class="username">{{ profile.username }}</h1>
              <el-tag v-if="isOwnProfile" size="small" type="success">我</el-tag>
            </div>

            <div class="bio-text" v-if="profile.bio">
              {{ profile.bio }}
            </div>
            <el-button v-else type="text" class="add-bio-btn" @click="showEditProfile = true" v-if="isOwnProfile">
              <svg class="edit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="5" y1="12" x2="19" y2="12" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              添加简介
            </el-button>

            <div class="meta-info">
              <span class="meta-item" v-if="profile.location">
                <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="10" r="3" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ profile.location }}
              </span>
              <span class="meta-item" v-if="profile.gender">
                <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M12 16v-4M12 8h.01" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ genderText }}
              </span>
            </div>

            <div class="stats-row">
              <div class="stat-item" @click="showFollowers = true">
                <span class="stat-value">{{ profile.follower_count || 0 }}</span>
                <span class="stat-label">粉丝</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item" @click="showFollowing = true">
                <span class="stat-value">{{ profile.following_count || 0 }}</span>
                <span class="stat-label">关注</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <span class="stat-value">{{ profile.post_count || 0 }}</span>
                <span class="stat-label">帖子</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <span class="stat-value">{{ profile.like_count || 0 }}</span>
                <span class="stat-label">获赞</span>
              </div>
            </div>

            <div class="action-row">
              <!-- 关注按钮（不是自己的主页时显示） -->
              <FollowButton
                v-if="!isOwnProfile"
                :userId="userId"
                :initialFollowing="profile.is_following"
                :initialFollowerCount="profile.follower_count"
                size="large"
              />

              <!-- 编辑资料按钮（自己的主页时显示） -->
              <el-button
                v-if="isOwnProfile"
                type="primary"
                size="large"
                @click="showEditProfile = true"
              >
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                编辑资料
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 内容标签页 -->
      <el-card class="profile-content-card">
        <el-tabs v-model="activeTab" class="profile-tabs" @tab-change="handleTabChange">
          <el-tab-pane label="帖子" name="posts">
            <div class="content-list">
              <div v-if="postsLoading" class="loading-container">
                <el-skeleton :rows="5" animated />
              </div>
              <div v-else-if="posts.length === 0" class="empty-container">
                <el-empty :description="isOwnProfile ? '暂无发布内容，去发第一条帖子吧~' : '暂无发布内容'" />
                <el-button v-if="isOwnProfile" type="primary" @click="$router.push('/admin/posts/new')">
                  发布帖子
                </el-button>
              </div>
              <div v-else class="post-list">
                <div v-for="post in posts" :key="post.post_id" class="post-item">
                  <div class="post-header">
                    <el-avatar :src="post.avatar_url || defaultAvatar" :size="40" class="post-avatar" />
                    <div class="post-info">
                      <div class="post-author">{{ post.username }}</div>
                      <div class="post-time">{{ formatTime(post.created_at) }}</div>
                    </div>
                  </div>
                  <div class="post-content">
                    <h4 class="post-title" v-if="post.title">{{ post.title }}</h4>
                    <p class="post-text">{{ truncateText(post.content, 200) }}</p>
                  </div>
                  <div class="post-footer">
                    <LikeButton
                      :targetType="'post'"
                      :targetId="post.post_id"
                      :initialCount="post.like_count"
                      :initialLiked="post.is_liked"
                      :showCount="true"
                    />
                    <span class="post-stat">
                      <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      {{ post.comment_count }}
                    </span>
                    <span class="post-stat">
                      <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke-linecap="round" stroke-linejoin="round"/>
                        <circle cx="12" cy="12" r="3" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      {{ post.view_count }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- 分页 -->
              <div class="pagination-container" v-if="posts.length > 0">
                <el-pagination
                  v-model:current-page="postsPage"
                  :page-size="postsPageSize"
                  :total="postsTotal"
                  layout="prev, pager, next"
                  @current-change="loadPosts"
                />
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="报表" name="reports">
            <div class="content-list">
              <div v-if="reportsLoading" class="loading-container">
                <el-skeleton :rows="5" animated />
              </div>
              <div v-else-if="reports.length === 0" class="empty-container">
                <el-empty :description="isOwnProfile ? '暂无发布的报表' : '暂无发布的报表'" />
              </div>
              <div v-else class="report-list">
                <div v-for="report in reports" :key="report.report_id" class="report-item">
                  <div class="report-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="14 2 14 8 20 8" stroke-linecap="round" stroke-linejoin="round"/>
                      <line x1="16" y1="13" x2="8" y2="13" stroke-linecap="round" stroke-linejoin="round"/>
                      <line x1="16" y1="17" x2="8" y2="17" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="10 9 9 9 8 9" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <div class="report-info">
                    <h4 class="report-name">{{ report.report_name }}</h4>
                    <p class="report-desc" v-if="report.description">{{ report.description }}</p>
                    <div class="report-meta">
                      <span class="report-type">{{ getReportTypeName(report.report_type) }}</span>
                      <span class="report-time">{{ formatTime(report.created_at) }}</span>
                    </div>
                  </div>
                  <div class="report-actions">
                    <LikeButton
                      :targetType="'report'"
                      :targetId="report.report_id"
                      :initialCount="report.like_count"
                      :initialLiked="report.is_liked"
                      :showCount="true"
                    />
                    <el-button type="primary" size="small" @click="viewReport(report.report_id)">
                      查看
                    </el-button>
                  </div>
                </div>
              </div>

              <!-- 分页 -->
              <div class="pagination-container" v-if="reports.length > 0">
                <el-pagination
                  v-model:current-page="reportsPage"
                  :page-size="reportsPageSize"
                  :total="reportsTotal"
                  layout="prev, pager, next"
                  @current-change="loadReports"
                />
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="点赞" name="likes" v-if="isOwnProfile">
            <div class="content-list">
              <div v-if="likesLoading" class="loading-container">
                <el-skeleton :rows="5" animated />
              </div>
              <div v-else-if="likes.length === 0" class="empty-container">
                <el-empty description="暂无点赞记录" />
              </div>
              <div v-else class="like-list">
                <div v-for="item in likes" :key="`${item.target_type}-${item.target_id}`" class="like-item">
                  <div class="like-icon-wrapper">
                    <svg class="like-icon-svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                    </svg>
                  </div>
                  <div class="like-info">
                    <span class="like-target-type">{{ getTargetTypeName(item.target_type) }}</span>
                    <span class="like-target-title">{{ item.target_title || `ID: ${item.target_id}` }}</span>
                    <span class="like-time">{{ formatTime(item.liked_at) }}</span>
                  </div>
                </div>
              </div>

              <!-- 分页 -->
              <div class="pagination-container" v-if="likes.length > 0">
                <el-pagination
                  v-model:current-page="likesPage"
                  :page-size="likesPageSize"
                  :total="likesTotal"
                  layout="prev, pager, next"
                  @current-change="loadLikes"
                />
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- 头像上传对话框 -->
    <AvatarUploadDialog
      v-model="showEditAvatar"
      :current-avatar="profile.avatar_url"
      @success="handleAvatarUploadSuccess"
    />

    <!-- 编辑资料对话框 -->
    <el-dialog
      v-model="showEditProfile"
      title="编辑资料"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="editForm" label-width="80px" label-position="left">
        <el-form-item label="个人简介">
          <el-input
            v-model="editForm.bio"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="介绍一下自己"
          />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="editForm.gender">
            <el-radio :label="0">保密</el-radio>
            <el-radio :label="1">男</el-radio>
            <el-radio :label="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="所在地">
          <el-input v-model="editForm.location" placeholder="例如：北京" maxlength="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditProfile = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateProfile" :loading="updating">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 粉丝/关注列表对话框 -->
    <el-dialog
      v-model="showFollowers"
      title="粉丝"
      width="400px"
    >
      <div class="follow-list">
        <el-empty v-if="!profile.follower_count || profile.follower_count === 0" description="暂无粉丝" />
        <div v-else v-for="i in profile.follower_count" :key="i" class="follow-item">
          <el-skeleton :rows="1" animated v-if="followersLoading" />
          <div v-else class="follow-item-content" v-if="followers[i-1]">
            <el-avatar :src="followers[i-1].avatar_url || defaultAvatar" :size="40" />
            <div class="follow-item-info">
              <div class="follow-item-name">{{ followers[i-1].username }}</div>
              <div class="follow-item-bio" v-if="followers[i-1].bio">{{ followers[i-1].bio }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="showFollowing"
      title="关注的人"
      width="400px"
    >
      <div class="follow-list">
        <el-empty v-if="!profile.following_count || profile.following_count === 0" description="暂无关注" />
        <div v-else v-for="i in profile.following_count" :key="i" class="follow-item">
          <el-skeleton :rows="1" animated v-if="followingLoading" />
          <div v-else class="follow-item-content" v-if="following[i-1]">
            <el-avatar :src="following[i-1].avatar_url || defaultAvatar" :size="40" />
            <div class="follow-item-info">
              <div class="follow-item-name">{{ following[i-1].username }}</div>
              <div class="follow-item-bio" v-if="following[i-1].bio">{{ following[i-1].bio }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import FollowButton from '@/components/FollowButton.vue'
import LikeButton from '@/components/LikeButton.vue'
import AvatarUploadDialog from '@/components/AvatarUploadDialog.vue'
import api from '@/api'

const route = useRoute()
const router = useRouter()

// 默认头像
const defaultAvatar = 'https://ui-avatars.com/api/?name={name}&background=random'

// 用户 ID（从路由参数获取）
const userId = ref(null)

// 用户资料
const profile = ref({
  user_id: null,
  username: '',
  avatar_url: null,
  bio: null,
  gender: 0,
  location: null,
  follower_count: 0,
  following_count: 0,
  post_count: 0,
  like_count: 0,
  is_following: false,
  is_me: false
})

// 是否自己的主页
const isOwnProfile = computed(() => profile.value.is_me)

// 头像文字
const avatarText = computed(() => {
  return profile.value.username ? profile.value.username.charAt(0).toUpperCase() : 'U'
})

// 性别文字
const genderText = computed(() => {
  const map = { 0: '保密', 1: '男', 2: '女' }
  return map[profile.value.gender] || ''
})

// 当前标签页
const activeTab = ref('posts')

// 帖子数据
const posts = ref([])
const postsPage = ref(1)
const postsPageSize = ref(10)
const postsTotal = ref(0)
const postsLoading = ref(false)

// 报表数据
const reports = ref([])
const reportsPage = ref(1)
const reportsPageSize = ref(10)
const reportsTotal = ref(0)
const reportsLoading = ref(false)

// 点赞数据
const likes = ref([])
const likesPage = ref(1)
const likesPageSize = ref(10)
const likesTotal = ref(0)
const likesLoading = ref(false)

// 粉丝/关注数据
const followers = ref([])
const following = ref([])
const followersLoading = ref(false)
const followingLoading = ref(false)
const showFollowers = ref(false)
const showFollowing = ref(false)

// 编辑资料
const showEditProfile = ref(false)
const showEditAvatar = ref(false)
const updating = ref(false)
const editForm = ref({
  avatar_url: '',
  bio: '',
  gender: 0,
  location: ''
})

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date

  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const month = 30 * day
  const year = 12 * month

  if (diff < minute) return '刚刚'
  if (diff < hour) return `${Math.floor(diff / minute)}分钟前`
  if (diff < day) return `${Math.floor(diff / hour)}小时前`
  if (diff < month) return `${Math.floor(diff / day)}天前`
  if (diff < year) return `${Math.floor(diff / month)}个月前`
  return `${Math.floor(diff / year)}年前`
}

// 截断文本
const truncateText = (text, length) => {
  if (!text) return ''
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

// 获取报表类型名称
const getReportTypeName = (type) => {
  const map = {
    table: '表格',
    chart: '图表',
    pivot: '透视表',
    dashboard: '仪表盘'
  }
  return map[type] || type
}

// 获取点赞目标类型名称
const getTargetTypeName = (type) => {
  const map = {
    post: '帖子',
    report: '报表',
    comment: '评论'
  }
  return map[type] || type
}

// 加载用户资料
const loadProfile = async () => {
  try {
    const result = await api.profile.getProfile(userId.value)
    if (result.success) {
      profile.value = result.data
    }
  } catch (error) {
    console.error('加载用户资料失败:', error)
    const message = error.detail?.message || error.message || '加载失败'
    ElMessage.error(message)
  }
}

// 加载帖子
const loadPosts = async () => {
  postsLoading.value = true
  try {
    const result = await api.profile.getUserContent(userId.value, {
      content_type: 'post',
      page: postsPage.value,
      page_size: postsPageSize.value
    })
    if (result.success) {
      posts.value = result.data.list
      postsTotal.value = result.data.total
    }
  } catch (error) {
    console.error('加载帖子失败:', error)
  } finally {
    postsLoading.value = false
  }
}

// 加载报表
const loadReports = async () => {
  reportsLoading.value = true
  try {
    const result = await api.profile.getUserContent(userId.value, {
      content_type: 'report',
      page: reportsPage.value,
      page_size: reportsPageSize.value
    })
    if (result.success) {
      reports.value = result.data.list
      reportsTotal.value = result.data.total
    }
  } catch (error) {
    console.error('加载报表失败:', error)
  } finally {
    reportsLoading.value = false
  }
}

// 加载点赞
const loadLikes = async () => {
  likesLoading.value = true
  try {
    const result = await api.profile.getUserLikes(userId.value, {
      page: likesPage.value,
      page_size: likesPageSize.value
    })
    if (result.success) {
      likes.value = result.data.list
      likesTotal.value = result.data.total
    }
  } catch (error) {
    console.error('加载点赞失败:', error)
  } finally {
    likesLoading.value = false
  }
}

// 加载粉丝列表
const loadFollowers = async () => {
  followersLoading.value = true
  try {
    const result = await api.follows.getFollowers(userId.value, 20, 0)
    if (result.success) {
      followers.value = result.data.list
    }
  } catch (error) {
    console.error('加载粉丝失败:', error)
  } finally {
    followersLoading.value = false
  }
}

// 加载关注列表
const loadFollowing = async () => {
  followingLoading.value = true
  try {
    const result = await api.follows.getFollowing(userId.value, 20, 0)
    if (result.success) {
      following.value = result.data.list
    }
  } catch (error) {
    console.error('加载关注失败:', error)
  } finally {
    followingLoading.value = false
  }
}

// 处理标签页切换
const handleTabChange = (tab) => {
  if (tab === 'posts') {
    loadPosts()
  } else if (tab === 'reports') {
    loadReports()
  } else if (tab === 'likes') {
    loadLikes()
  }
}

// 处理头像上传成功
const handleAvatarUploadSuccess = (avatarUrl) => {
  profile.value.avatar_url = avatarUrl
  editForm.value.avatar_url = avatarUrl
}

// 更新资料
const handleUpdateProfile = async () => {
  updating.value = true
  try {
    const result = await api.profile.updateProfile(editForm.value)
    if (result.success) {
      profile.value = result.data
      showEditProfile.value = false
      ElMessage.success('保存成功')
    }
  } catch (error) {
    console.error('更新资料失败:', error)
    const message = error.detail?.message || error.message || '保存失败'
    ElMessage.error(message)
  } finally {
    updating.value = false
  }
}

// 查看报表
const viewReport = (reportId) => {
  router.push(`/admin/reports/${reportId}`)
}

// 初始化
onMounted(async () => {
  // 从路由参数获取用户 ID
  userId.value = parseInt(route.params.userId) || null

  if (!userId.value) {
    // 如果没有用户 ID，尝试获取当前用户
    try {
      const result = await api.profile.getMyProfile()
      if (result.success) {
        userId.value = result.data.user_id
        profile.value = result.data
        loadPosts()
      }
    } catch (error) {
      console.error('获取当前用户失败:', error)
      ElMessage.error('请先登录')
      router.push('/login')
      return
    }
  } else {
    await loadProfile()
    loadPosts()
  }
})

// 监听对话框打开
watch(showFollowers, (val) => {
  if (val) loadFollowers()
})

watch(showFollowing, (val) => {
  if (val) loadFollowing()
})

// 监听编辑对话框打开
watch(showEditProfile, (val) => {
  if (val) {
    editForm.value = {
      avatar_url: profile.value.avatar_url || '',
      bio: profile.value.bio || '',
      gender: profile.value.gender || 0,
      location: profile.value.location || ''
    }
  }
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 24px;
}

.profile-container {
  max-width: 900px;
  margin: 0 auto;
}

/* 头部卡片 */
.profile-header-card {
  margin-bottom: 24px;
  border-radius: 16px;
  overflow: hidden;
}

.profile-header {
  display: flex;
  gap: 32px;
  padding: 24px;
}

.avatar-section {
  flex-shrink: 0;
}

.avatar-wrapper {
  position: relative;
  display: inline-block;
}

.user-avatar {
  border: 4px solid #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.avatar-text {
  font-size: 48px;
  font-weight: 600;
  color: #ffffff;
}

.edit-avatar-btn {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.edit-icon {
  width: 14px;
  height: 14px;
}

.info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.username-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.bio-text {
  font-size: 16px;
  color: #64748b;
  line-height: 1.6;
}

.add-bio-btn {
  color: #64748b;
  font-size: 14px;
  padding: 0;
}

.add-bio-btn .edit-icon {
  width: 16px;
  height: 16px;
  margin-right: 4px;
  vertical-align: middle;
}

.meta-info {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #64748b;
}

.meta-icon {
  width: 16px;
  height: 16px;
  color: #94a3b8;
}

.stats-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 8px;
  transition: background 0.2s;
}

.stat-item:hover {
  background: #f1f5f9;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: #e2e8f0;
}

.action-row {
  display: flex;
  gap: 12px;
  padding-top: 8px;
}

.btn-icon {
  width: 18px;
  height: 18px;
  margin-right: 6px;
  vertical-align: middle;
}

/* 内容卡片 */
.profile-content-card {
  border-radius: 16px;
}

.profile-tabs {
  padding: 0;
}

.content-list {
  min-height: 300px;
  padding: 24px;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.empty-container {
  flex-direction: column;
  gap: 16px;
}

/* 帖子列表 */
.post-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.post-item {
  padding: 20px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #ffffff;
  transition: box-shadow 0.2s;
}

.post-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.post-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.post-avatar {
  flex-shrink: 0;
}

.post-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.post-author {
  font-weight: 600;
  color: #1e293b;
}

.post-time {
  font-size: 13px;
  color: #94a3b8;
}

.post-content {
  margin-bottom: 16px;
}

.post-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.post-text {
  font-size: 15px;
  color: #475569;
  line-height: 1.7;
  margin: 0;
}

.post-footer {
  display: flex;
  align-items: center;
  gap: 20px;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

.post-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #64748b;
}

.stat-icon {
  width: 18px;
  height: 18px;
  color: #94a3b8;
}

/* 报表列表 */
.report-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.report-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #ffffff;
  transition: box-shadow 0.2s;
}

.report-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.report-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 12px;
  flex-shrink: 0;
}

.report-icon svg {
  width: 28px;
  height: 28px;
  color: #ffffff;
}

.report-info {
  flex: 1;
  min-width: 0;
}

.report-name {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.report-type {
  font-size: 12px;
  color: #3b82f6;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 4px;
}

.report-time {
  font-size: 13px;
  color: #94a3b8;
}

.report-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* 点赞列表 */
.like-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.like-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
}

.like-icon-wrapper {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fca5a5 0%, #ef4444 100%);
  border-radius: 50%;
  flex-shrink: 0;
}

.like-icon-svg {
  width: 20px;
  height: 20px;
  color: #ffffff;
}

.like-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.like-target-type {
  font-size: 13px;
  color: #3b82f6;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 4px;
}

.like-target-title {
  font-size: 14px;
  color: #1e293b;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.like-time {
  font-size: 13px;
  color: #94a3b8;
}

/* 分页 */
.pagination-container {
  display: flex;
  justify-content: center;
  padding-top: 24px;
}

/* 粉丝/关注列表 */
.follow-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.follow-item {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.follow-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.follow-item-info {
  flex: 1;
  min-width: 0;
}

.follow-item-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 15px;
}

.follow-item-bio {
  font-size: 13px;
  color: #64748b;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 响应式 */
@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .meta-info {
    justify-content: center;
  }

  .stats-row {
    justify-content: center;
  }

  .action-row {
    justify-content: center;
  }

  .report-item {
    flex-direction: column;
    text-align: center;
  }

  .report-meta {
    justify-content: center;
  }

  .report-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>
