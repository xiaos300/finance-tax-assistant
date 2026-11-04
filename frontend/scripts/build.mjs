// Avoid the Windows native recursive removal path observed to terminate Node 24.8.
// Only remove the validated, generated dist tree; never follow symbolic links.
import { existsSync, lstatSync, readdirSync, realpathSync, rmdirSync, unlinkSync } from 'node:fs'
import { dirname, join, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const frontend = realpathSync(resolve(dirname(fileURLToPath(import.meta.url)), '..'))
const output = join(frontend, 'dist')

function validate(path) {
  if (lstatSync(path).isSymbolicLink()) throw new Error('Refusing linked build output')
  const actual = realpathSync(path)
  if (actual !== output && !actual.startsWith(output + sep)) {
    throw new Error('Build cleanup target escapes dist')
  }
}

function inspect(path) {
  validate(path)
  if (lstatSync(path).isDirectory()) {
    for (const entry of readdirSync(path)) inspect(join(path, entry))
  }
}

function clean(path) {
  validate(path)
  if (lstatSync(path).isDirectory()) {
    for (const entry of readdirSync(path)) clean(join(path, entry))
    if (path !== output) rmdirSync(path)
  } else {
    unlinkSync(path)
  }
}

if (existsSync(output)) {
  // Preflight the entire tree before any removal.
  inspect(output)
  console.log(`Cleaning generated output: ${output}`)
  clean(output)
}
const result = spawnSync(process.execPath, [join(frontend, 'node_modules/vite/bin/vite.js'), 'build', '--emptyOutDir=false'], {
  cwd: frontend, stdio: 'inherit',
})
if (result.error) throw result.error
process.exit(result.status ?? 1)
