#### Run the test

```bash
# clean the redis server
redis-cli flushall

# run the test
python -m unittest test_web

# or use this to run specific test
python -m unittest test_web.TestWeb.<test_case>
```