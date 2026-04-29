<template>
  <div class="comment-list">
    <!-- 评论表单 -->
    <div v-if="showForm" class="comment-form-wrapper">
      <CommentForm
        :target-type="targetType"
        :target-id="targetId"
        @submitted="onCommentSubmitted"
      />
    </div>

    <!-- 评论列表 -->
    <div class="comments-container">
      <div v-if="loading && comments.length === 0" class="loading-state">
        <el-skeleton :rows="3" animated />
      </div>

      <div v-else-if="comments.length === 0" class="empty-state">
        <el-empty description="暂无评论，快来抢沙发吧" />
      </div>

      <div v-else class="comments-list">
        <div v-for="comment in comments" :key="comment.comment_id" class="comment-wrapper">
          <CommentItem
            :comment="comment"
            :target-type="targetType"
            :target-id="targetId"
            :currentUserId="currentUserId"
            @reply="onReply"
            @edit="onEdit"
            @delete="onDelete"
            @like="onLike"
          />

          <!-- 回复列表 -->
          <div v-if="comment.reply_count > 0 && expandedComments[comment.comment_id]" class="replies-list">
            <div v-for="reply in replyLists[comment.comment_id] || []" :key="reply.comment_id">
              <CommentItem
                :comment="reply"
                :target-type="targetType"
                :target-id="targetId"
                :currentUserId="currentUserId"
                :is-reply="true"
                @reply="onReply"
                @edit="onEdit"
                @delete="onDeleteReply"
                @like="onLike"
              />
            </div>
            <div v-if="replyCounts[comment.comment_id] > (replyLists[comment.comment_id] || []).length" class="load-more-replies">
              <el-button link type="primary" @click="loadMoreReplies(comment.comment_id)">
                查看更多回复 ({{ replyCounts[comment.comment_id] - (replyLists[comment.comment_id] || []).length }})
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import CommentForm from './CommentForm.vue'
import CommentItem from './CommentItem.vue'
import commentsApi from '@/api/comments'

const { getList: getComments, getReplies } = commentsApi

const props = defineProps({
  targetType: {
    type: String,
    required: true,
    validator: (val) => ['post', 'report'].includes(val)
  },
  targetId: {
    type: Number,
    required: true
  },
  showForm: {
    type: Boolean,
    default: true
  },
  currentUserId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['comment-count-change'])

const comments = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const sortBy = ref('created_at')

// 回复相关状态
const expandedComments = reactive({})
const replyLists = reactive({})
const replyCounts = reactive({})
const replyPages = reactive({})

// 加载评论
const loadComments = async () => {
  loading.value = true
  try {
    const result = await getComments({
      target_type: props.targetType,
      target_id: props.targetId,
      page: currentPage.value,
      page_size: pageSize.value,
      sort_by: sortBy.value
    })

    comments.value = result.data.list || []
    total.value = result.data.total || 0

    // 初始化回复状态
    comments.value.forEach(comment => {
      if (comment.reply_count > 0) {
        replyCounts[comment.comment_id] = comment.reply_count
        replyLists[comment.comment_id] = []
        replyPages[comment.comment_id] = 1
      }
    })

    emit('comment-count-change', total.value)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail?.message || '加载评论失败')
  } finally {
    loading.value = false
  }
}

// 加载回复
const loadReplies = async (commentId) => {
  try {
    const page = replyPages[commentId] || 1
    const result = await getReplies({
      parent_id: commentId,
      page: page,
      page_size: 10
    })

    const newReplies = result.data.list || []
    if (!replyLists[commentId]) {
      replyLists[commentId] = []
    }
    replyLists[commentId] = [...replyLists[commentId], ...newReplies]
  } catch (error) {
    ElMessage.error('加载回复失败')
  }
}

// 展开/收起回复
const toggleReplies = async (commentId) => {
  if (expandedComments[commentId]) {
    expandedComments[commentId] = false
  } else {
    expandedComments[commentId] = true
    if (!replyLists[commentId] || replyLists[commentId].length === 0) {
      await loadReplies(commentId)
    }
  }
}

// 加载更多回复
const loadMoreReplies = async (commentId) => {
  replyPages[commentId] = (replyPages[commentId] || 1) + 1
  await loadReplies(commentId)
}

// 评论成功
const onCommentSubmitted = (newComment) => {
  comments.value.unshift(newComment)
  total.value++
  if (newComment.reply_count > 0) {
    replyCounts[newComment.comment_id] = newComment.reply_count
    replyLists[newComment.comment_id] = []
  }
  ElMessage.success('评论成功')
}

// 回复成功
const onReply = (newReply) => {
  // 更新父评论的回复数
  const parentComment = comments.value.find(c => c.comment_id === newReply.parent_id)
  if (parentComment) {
    parentComment.reply_count = (parentComment.reply_count || 0) + 1
  }

  // 添加到回复列表
  if (!replyLists[newReply.parent_id]) {
    replyLists[newReply.parent_id] = []
    expandedComments[newReply.parent_id] = true
  }
  replyLists[newReply.parent_id].push(newReply)
  replyCounts[newReply.parent_id] = (replyCounts[newReply.parent_id] || 0) + 1
}

// 编辑成功
const onEdit = (updatedComment) => {
  const index = comments.value.findIndex(c => c.comment_id === updatedComment.comment_id)
  if (index !== -1) {
    comments.value[index] = updatedComment
  }
}

// 删除成功
const onDelete = (commentId) => {
  const index = comments.value.findIndex(c => c.comment_id === commentId)
  if (index !== -1) {
    comments.value.splice(index, 1)
    total.value--
    emit('comment-count-change', total.value)
  }
}

// 删除回复
const onDeleteReply = (commentId) => {
  // 查找并更新父评论的回复数
  const parentComment = comments.value.find(c => {
    return replyLists[c.comment_id]?.some(r => r.comment_id === commentId)
  })
  if (parentComment) {
    parentComment.reply_count = Math.max(0, (parentComment.reply_count || 0) - 1)
    if (replyLists[parentComment.comment_id]) {
      replyLists[parentComment.comment_id] = replyLists[parentComment.comment_id].filter(
        r => r.comment_id !== commentId
      )
    }
    if (replyCounts[parentComment.comment_id]) {
      replyCounts[parentComment.comment_id] = Math.max(0, replyCounts[parentComment.comment_id] - 1)
    }
  }
}

// 点赞成功
const onLike = (commentId) => {
  // 更新本地状态
  const comment = comments.value.find(c => c.comment_id === commentId)
  if (comment) {
    comment.user_liked = !comment.user_liked
    comment.like_count = comment.user_liked
      ? (comment.like_count || 0) + 1
      : Math.max(0, (comment.like_count || 0) - 1)
  }

  // 在回复列表中查找
  Object.values(replyLists).forEach(list => {
    const reply = list?.find(r => r.comment_id === commentId)
    if (reply) {
      reply.user_liked = !reply.user_liked
      reply.like_count = reply.user_liked
        ? (reply.like_count || 0) + 1
        : Math.max(0, (reply.like_count || 0) - 1)
    }
  })
}

// 分页事件
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  loadComments()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  loadComments()
}

// 暴露刷新方法
const refresh = () => {
  loadComments()
}

defineExpose({ refresh })

onMounted(() => {
  loadComments()
})
</script>

<style scoped>
.comment-list {
  background: #fff;
  border-radius: 8px;
}

.comment-form-wrapper {
  margin-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 16px;
}

.comments-container {
  min-height: 200px;
}

.loading-state,
.empty-state {
  padding: 40px 0;
  text-align: center;
}

.comments-list {
  margin-top: 16px;
}

.comment-wrapper {
  border-bottom: 1px solid #f0f0f0;
}

.comment-wrapper:last-child {
  border-bottom: none;
}

.replies-list {
  margin-left: 52px;
  padding: 8px 0;
}

.load-more-replies {
  margin-top: 8px;
  padding-left: 12px;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>
