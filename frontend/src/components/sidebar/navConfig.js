import { 
  HomeIcon,
  ClipboardDocumentListIcon,
  ComputerDesktopIcon,
  TagIcon,
  KeyIcon,
  UserIcon,
  AdjustmentsHorizontalIcon,
  DocumentTextIcon,
  ServerIcon
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
      { name: 'List', path: '/jobs', icon: ClipboardDocumentListIcon },
      { name: 'Dashboard', path: '/jobs-dashboard', icon: HomeIcon }
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
    name: 'Backups',
    icon: ServerIcon,
    children: [
      { name: 'Snapshots', path: '/backups/snapshots', icon: DocumentTextIcon },
      { name: 'Schedules', path: '/backups/schedules', icon: ClipboardDocumentListIcon },
      { name: 'Audit Logs', path: '/backups/audit-logs', icon: DocumentTextIcon },
      { name: 'Diff', path: '/backups/diff', icon: AdjustmentsHorizontalIcon }
    ]
  },
  {
    name: 'Logs',
    path: '/logs',
    icon: DocumentTextIcon
  }
];