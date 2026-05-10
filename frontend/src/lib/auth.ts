/**
 * Auth wrapper.
 *
 * Behavior:
 * - If VITE_FIREBASE_CONFIG is set, dynamically loads firebase/auth and
 *   tracks the real Firebase user.
 * - Otherwise stays in dev mode and provides a fixed dev user with a
 *   "dev" bearer token that the backend honors when ENVIRONMENT=dev.
 */

type AuthUser = {
  id: string
  email: string
  displayName: string | null
  isDev: boolean
  token: string
}

const DEV_USER: AuthUser = {
  id: '00000000-0000-0000-0000-000000000001',
  email: 'dev@cofre.local',
  displayName: 'Jesse (dev)',
  isDev: true,
  token: 'dev',
}

let currentUser: AuthUser | null = DEV_USER
const listeners = new Set<(u: AuthUser | null) => void>()

export function getCurrentUser(): AuthUser | null {
  return currentUser
}

export function getAuthToken(): string | null {
  return currentUser?.token ?? null
}

export function onAuthChange(cb: (u: AuthUser | null) => void): () => void {
  listeners.add(cb)
  cb(currentUser)
  return () => listeners.delete(cb)
}

function emit() {
  for (const cb of listeners) cb(currentUser)
}

// If a firebase config is provided at build time, swap in real auth.
const FIREBASE_CONFIG = (import.meta.env.VITE_FIREBASE_CONFIG as string | undefined) || ''

if (FIREBASE_CONFIG) {
  ;(async () => {
    try {
      const cfg = JSON.parse(FIREBASE_CONFIG)
      // String variables prevent Vite from statically resolving these
      // at build time when firebase isn't installed in dev mode.
      const appPkg = 'firebase/app'
      const authPkg = 'firebase/auth'
      const fbApp: any = await import(/* @vite-ignore */ appPkg)
      const fbAuth: any = await import(/* @vite-ignore */ authPkg)
      const app = fbApp.initializeApp(cfg)
      const auth = fbAuth.getAuth(app)
      fbAuth.onAuthStateChanged(auth, async (fbUser: any) => {
        if (!fbUser) {
          currentUser = null
        } else {
          const token = await fbUser.getIdToken()
          currentUser = {
            id: fbUser.uid,
            email: fbUser.email ?? '',
            displayName: fbUser.displayName,
            isDev: false,
            token,
          }
        }
        emit()
      })
    } catch (e) {
      console.error('firebase init failed; staying in dev mode', e)
    }
  })()
}
