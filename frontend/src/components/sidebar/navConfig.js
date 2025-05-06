import { 
  HomeIcon,
  ClipboardDocumentListIcon,
  ComputerDesktopIcon,
  TagIcon,
  KeyIcon,
  UserIcon,
  AdjustmentsHorizontalIcon,
  DocumentTextIcon
} from '@heroicons/vue/24/outline'

export default [
  {
    name: 'Dashboard',
    path: '/dashboard',
    icon: HomeIcon
  },
  {
    name: 'Jobs',
    icon: ClipboardDocumentListIcon,
    children: [
      { name: 'List', path: '/jobs' },
      { name: 'Dashboard', path: '/jobs-dashboard' }
    ]
  },
  {
    name: 'Devices',
    path: '/devices',
    icon: ComputerDesktopIcon
  },
  {
    name: 'Tags',
    path: '/tags',
    icon: TagIcon
  },
  {
    name: 'Credentials',
    path: '/credentials',
    icon: KeyIcon
  },
  {
    name: 'Users',
    path: '/users',
    icon: UserIcon
  },
  {
    name: 'Config Diff',
    path: '/config-diff',
    icon: AdjustmentsHorizontalIcon
  },
  {
    name: 'Logs',
    path: '/logs',
    icon: DocumentTextIcon
  }
]; 