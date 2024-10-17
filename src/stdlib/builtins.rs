use crate::std_mod;

std_mod!
{
	ret;
	std_fn!
	{
		none return_none()
		{
			self.path = 0;
			Value::new_none()
		}
	}
	std_fn!
	{
		any return_any(any x0)
		{
			self.path = 0;
			x0
		}
	}
}

// def return_none(task):
	
// 	if task.caller:
// 		task.restore() # Restore namespace of calling routine
// 	else:
// 		task.path = 0 # End task
// 	return None # Returns null

// def return_any(task, sentinel):
	
// 	task.properties = typedef(task.final)
// 	if task.caller:
// 		task.restore() # Restore namespace of calling routine
// 	else:
// 		task.path = 0 # End task
// 	task.values[task.op.address] = sentinel # Different return address
// 	return sentinel