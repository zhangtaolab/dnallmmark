#!/usr/bin/env node

/**
 * Generate tasks.json index file from task_performance directory
 * Extracts metadata from each task file to create lightweight index
 */

const fs = require('fs');
const path = require('path');

const TASK_PERFORMANCE_DIR = path.join(__dirname, '..', 'dnallm-mark', 'data', 'task_performance');
const OUTPUT_FILE = path.join(__dirname, '..', 'dnallm-mark', 'data', 'tasks.json');

function generateTaskIndex() {
  console.log('Generating tasks.json index...');
  
  // Read all task files
  const files = fs.readdirSync(TASK_PERFORMANCE_DIR)
    .filter(file => file.endsWith('_task_performance.json'))
    .sort();
  
  console.log(`Found ${files.length} task files`);
  
  const tasks = files.map(file => {
    const filePath = path.join(TASK_PERFORMANCE_DIR, file);
    const content = fs.readFileSync(filePath, 'utf8');
    const data = JSON.parse(content);
    
    // Extract task ID from filename
    const taskId = file.replace('_task_performance.json', '');
    
    // Format display name (replace underscores with spaces)
    const displayName = taskId.replace(/_/g, ' ');
    
    return {
      id: taskId,
      name: taskId,
      displayName: displayName,
      species: data.info?.species || 'Unknown',
      type: data.info?.type || 'unknown',
      labels: data.info?.labels || 0,
      length: data.info?.length || 0,
      metric: data.info?.metric || 'accuracy',
      fileName: file
    };
  });
  
  const index = {
    version: '1.0.0',
    generatedAt: new Date().toISOString().split('T')[0],
    count: tasks.length,
    tasks: tasks
  };
  
  // Write output
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(index, null, 2));
  
  console.log(`✓ Generated tasks.json with ${tasks.length} tasks`);
  console.log(`  Output: ${OUTPUT_FILE}`);
  console.log(`  Size: ${(fs.statSync(OUTPUT_FILE).size / 1024).toFixed(2)} KB`);
  
  // Show sample
  console.log('\nSample tasks:');
  tasks.slice(0, 3).forEach(task => {
    console.log(`  - ${task.id} (${task.species}, ${task.type}, ${task.metric})`);
  });
}

generateTaskIndex();
