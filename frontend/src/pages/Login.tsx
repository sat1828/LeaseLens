import { motion } from 'framer-motion'
import AuthModal from '../components/auth/AuthModal'

export default function Login() {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-white border border-slate-100 rounded-2xl shadow-sm p-8"
      >
        <AuthModal defaultMode="login" />
      </motion.div>
    </div>
  )
}
