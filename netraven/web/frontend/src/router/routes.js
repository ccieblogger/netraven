import TagList from '@/views/TagList.vue'
import TagRuleList from '@/views/TagRuleList.vue'
import CredentialList from '@/views/CredentialList.vue'

// Main routes
const routes = [
  {
    path: '/tags',
    name: 'Tags',
    component: TagList,
    meta: { 
      requiresAuth: true,
      title: 'Tags'
    }
  },
  {
    path: '/tag-rules',
    name: 'TagRules',
    component: TagRuleList,
    meta: { 
      requiresAuth: true,
      title: 'Tag Rules'
    }
  },
  {
    path: '/credentials',
    name: 'Credentials',
    component: CredentialList,
    meta: { 
      requiresAuth: true,
      title: 'Credentials'
    }
  },
] 